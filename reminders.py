from application import handlers, Application
import os


app = Application(handlers, os.environ, debug=True)
db = app.db
celery = app.celery()





import tasks

login_session = app.login_session
client_id = app.google_client_id