from flask.views import MethodView
from flask import render_template
from models.appointment import Appointment, User
from forms.new_appointment import NewAppointmentForm
from flask import request, redirect, url_for
import reminders
import arrow

from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from models.appointment import Base, User
from flask import session as login_session
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
        state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        reminders.login_session['state'] = state
        return render_template('login/login.html', STATE=state)

class Login(MethodView):

    def post(self):
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

        reminders.login_session['username'] = data['name']
        reminders.login_session['picture'] = data['picture']
        reminders.login_session['google_id'] = data['id']

        # check if user is already in the database
        if getUserID(reminders.login_session['google_id']) is None:
            createUser(reminders.login_session)
        else: # not a new user
            pass # might add some additional logic here later
        

        output = ''
        output += '<h1>Welcome, '
        output += reminders.login_session['username']
        output += '!</h1>'
        output += '<img src="'
        output += reminders.login_session['picture']
        output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
        flash("you are now logged in as {0}".format(reminders.login_session['username']))
        print "done!"
        return output


class AppointmentResourceDelete(MethodView):

    def post(self, id):
        appt = reminders.db.session.query(Appointment).filter_by(id=id).one()
        reminders.db.session.delete(appt)
        reminders.db.session.commit()

        return redirect(url_for('appointment.index'), code=303)


class Dashboard(MethodView):

    def get(self):
        return 'under construction'


class AppointmentResourceCreate(MethodView):

    def post(self):
        form = NewAppointmentForm(request.form)

        if form.validate():
            from tasks import send_sms_reminder

            appt = Appointment(**form.data)
            appt.time = arrow.get(appt.time, appt.timezone).to('utc').naive

            reminders.db.session.add(appt)
            reminders.db.session.commit()
            send_sms_reminder.apply_async(
                args=[appt.id], eta=appt.get_notification_time())

            return redirect(url_for('appointment.index'), code=303)
        else:
            return render_template('appointments/new.html', form=form), 400


class AppointmentResourceIndex(MethodView):

    def get(self):
        all_appointments = reminders.db.session.query(Appointment).all()
        return render_template('appointments/index.html',
                               appointments=all_appointments)


class AppointmentFormResource(MethodView):

    def get(self):
        form = NewAppointmentForm()
        return render_template('appointments/new.html', form=form)
