from application import handlers, Application
import os

app = Application(handlers, os.environ, debug=True)
db = app.db
login_session = app.login_session
client_id = app.google_client_id
celery = app.celery()

import tasks
