from flask.views import MethodView
from flask import render_template
from models.appointment import Appointment, Base, User
from forms.new_appointment import NewAppointmentForm
from forms.edit_user import EditUserForm
from flask import request, redirect, url_for
import reminders
import arrow


from flask import Flask, render_template, request, redirect, jsonify, url_for, flash

import random
import string

import datetime

# IMPORTS FOR THIS STEP
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

# move logic for accessing user database to different file

def createUser(login_session):
    newUser = User(name=login_session['username'], google_id=login_session[
                   'google_id'], picture=login_session['picture'])
    reminders.db.session.add(newUser)
    reminders.db.session.commit()
    user = reminders.db.session.query(User).filter_by(google_id=login_session['google_id']).one()
    return user.id

def getUserInfo(user_id):
    user = reminders.db.session.query(User).filter_by(id=user_id).one()
    return user

def getUserID(google_id):
    try:
        user = reminders.db.session.query(User).filter_by(google_id=google_id).one()
        return user.id
    except:
        return None

#login session can be accessed at reminders.login_session
#client_id is reminders.client_id



       

class Splash(MethodView):

    def get(self):
        return render_template('login/splash.html')


class ShowLogin(MethodView):

    def get(self):
        reminders.login_session.clear()
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        reminders.login_session['state'] = state
        print reminders.login_session
        return render_template('login/login.html', STATE=state)

class LogoutAjax(MethodView):

    def get(self):
        try:
            revoke = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % reminders.login_session['access_token']

            reminders.login_session.clear()

            return render_template('login/logout.html', revoke = revoke)
        except:
            print "No access token"
            reminders.login_session.clear()
            return redirect(url_for('splash'))

class Logout(MethodView):

    def get(self):
        print reminders.login_session
        access_token = reminders.login_session.get('access_token')
        print 'In gdisconnect access token is {0}'.format(access_token)
        if access_token is None:
            print 'Access Token is None'
            response = make_response(json.dumps('Current user not connected.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % reminders.login_session['access_token']
        h = httplib2.Http()
        result = h.request(url, 'GET')[0]
        print 'result is '
        print result
        if result['status'] == '200':
            username = getUserInfo(reminders.login_session['user_id']).name
            del reminders.login_session['access_token'] 
            del reminders.login_session['google_id']
            del reminders.login_session['user_id']
            #response = make_response(json.dumps('You have logged out'), 200)
            #response.headers['Content-Type'] = 'application/json'
            #return response
            flash('User {0} has been logged out'.format(username))
            return redirect(url_for('splashPage'))
        else:
      
          response = make_response(json.dumps('Failed to revoke token for given user.', 400))
          response.headers['Content-Type'] = 'application/json'
          return response

class Login(MethodView):

    def post(self):
        print 'request args', request.args.get('state')
        print 'reminders login', reminders.login_session['state']
        if request.args.get('state') != reminders.login_session['state']:
            response = make_response(json.dumps('Invalid state parameter.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response
        # Obtain authorization code
        code = request.data

        try:
            # Upgrade the authorization code into a credentials object
            oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
            oauth_flow.redirect_uri = 'postmessage'
            credentials = oauth_flow.step2_exchange(code)
        except FlowExchangeError:
            response = make_response(
                json.dumps('Failed to upgrade the authorization code.'), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Check that the access token is valid.
        access_token = credentials.access_token
        url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={0}'.format(access_token))
        h = httplib2.Http()
        result = json.loads(h.request(url, 'GET')[1])
        # If there was an error in the access token info, abort.
        if result.get('error') is not None:
            response = make_response(json.dumps(result.get('error')), 500)
            response.headers['Content-Type'] = 'application/json'

        #Verify that the access token is used for the intended user.
        u_id = credentials.id_token['sub']
        if result['user_id'] != u_id:
            response = make_response(
                json.dumps("Token's user ID doesn't match given user ID."), 401)
            response.headers['Content-Type'] = 'application/json'
            return response

        # Verify that the access token is valid for this app.
        if result['issued_to'] != reminders.client_id:
            response = make_response(
                json.dumps("Token's client ID does not match app's."), 401)
            print "Token's client ID does not match app's."
            response.headers['Content-Type'] = 'application/json'
            return response

        #stored_access_token = login_session.get('access_token')
        #stored_gplus_id = login_session.get('user_id')
        #if stored_access_token is not None and u_id == stored_gplus_id:
        #    response = make_response(json.dumps('Current user is already connected.'), 200)
        #    response.headers['Content-Type'] = 'application/json'
        #    return response

        # Store the access token in the session for later use.
        reminders.login_session['access_token'] = credentials.access_token

        print 'login session access token', reminders.login_session['access_token']

        # Get user info
        userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
        params = {'access_token': credentials.access_token, 'alt': 'json'}
        answer = requests.get(userinfo_url, params=params)

        data = answer.json()
        print data

        reminders.login_session['google_id'] = data['id']

        # check if user is already in the database
        if getUserID(reminders.login_session['google_id']) is None:
            createUser(reminders.login_session)
        else: # not a new user
            pass # might add some additional logic here later

        
        current_user = reminders.db.session.query(User).filter_by(google_id=reminders.login_session['google_id']).one()
        reminders.login_session['user_id'] = current_user.id
        print current_user.id
        

        output = ''
        output += '<h1>Welcome, '
        output += current_user.name
        output += '!</h1>'
        output += '<img src="'
        output += current_user.picture
        output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
        flash("you are now logged in as {0}".format(current_user.name))
        print "done!"
        return output


class AppointmentResourceDelete(MethodView):

    def post(self, id):
        appt = reminders.db.session.query(Appointment).filter_by(id=id).one()
        reminders.db.session.delete(appt)
        reminders.db.session.commit()

        return redirect(url_for('appointment.index'), code=303)


class UserEdit(MethodView):

    def post(self):
        form = EditUserForm(request.form)

        if form.validate():

            user = getUserInfo(reminders.login_session['user_id'])
            user.name = request.form['name']
            user.phone = request.form['phone_number']
            user.picture = request.form['image_link']

            reminders.db.session.add(user)
            reminders.db.session.commit()

            flash('User info updated!')
            return redirect(url_for('appointment.index'), code=303)
        else:
            return render_template('user/edit.html', form=form), 400

class UserFormEdit(MethodView):

    def get(self):
        form = EditUserForm()
        user = getUserInfo(reminders.login_session['user_id'])
        form.name.default = user.name
        form.phone_number.default = user.phone
        form.image_link.default = user.picture
        form.process()
        return render_template('user/edit.html', form=form)

class DeleteUser(MethodView):

    def get(self):
        user = getUserInfo(reminders.login_session['user_id'])
        appointments = reminders.db.session.query(Appointment).filter_by(user_id=user.id).all()
        for appt in appointments:
            reminders.db.session.delete(appt)
            reminders.db.session.commit()

        reminders.db.session.delete(user)
        reminders.db.session.commit()

        del reminders.login_session['access_token'] 
        del reminders.login_session['google_id']
        del reminders.login_session['user_id']
        return redirect(url_for('appointment.index'))


class DeleteUserForm(MethodView):

    def get(self):
        if reminders.login_session.get('user_id') is not None:
            return render_template('user/delete.html')
        else:
            return redirect(url_for('splash'))
        


class AppointmentResourceCreate(MethodView):

    def post(self):
        form = NewAppointmentForm(request.form)
        

        if form.validate():
            from tasks import send_sms_reminder

            appt = Appointment(**form.data)
            appt.time = arrow.get(appt.time, appt.timezone).to('utc').naive
            appt.user_id = reminders.login_session['user_id']

            reminders.db.session.add(appt)
            reminders.db.session.commit()
            send_sms_reminder.apply_async(
                args=[appt.id], eta=appt.get_notification_time())

            return redirect(url_for('appointment.index'), code=303)
        else:
            return render_template('appointments/new.html', form=form), 400


class AppointmentResourceIndex(MethodView):

    def get(self):
        if reminders.login_session.get('user_id') is not None:
            all_appointments = reminders.db.session.query(Appointment).filter_by(user_id = reminders.login_session['user_id'])
            return render_template('appointments/index.html', appointments=all_appointments)
        else:
            return redirect(url_for('splash'))


class AppointmentFormResource(MethodView):

    def get(self):
        form = NewAppointmentForm()
        user = getUserInfo(reminders.login_session['user_id'])
        form.name.default = user.name
        form.phone_number.default = user.phone
        form.process()
        return render_template('appointments/new.html', form=form)
