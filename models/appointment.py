from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, DateTime, String, ForeignKey
#from sqlalchemy.orm import relationship
import arrow

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    google_id = Column(String(200))
    picture = Column(String(200))
    email = Column(String(200))
    phone = Column(String(50))

    def __init__(self, name, google_id, picture=None, email=None, phone=None):
        self.name = name
        self.google_id = google_id
        self.picture = picture
        self.email = email
        self.phone = phone

    def __repr__(self):
        return '<User {0}:{1}>'.format(self.name,self.google_id)



class Appointment(Base):
    __tablename__ = 'appointments'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    reminder = Column(String(250), nullable=False)
    phone_number = Column(String(50), nullable=False)
    delta = Column(Integer, nullable=False)
    time = Column(DateTime, nullable=False)
    timezone = Column(String(50), nullable=False)

    #user = relationship(User)
    user_id = Column(Integer, ForeignKey('User.id'))


    def __init__(self, name, reminder, phone_number, delta, time, timezone):
        self.name = name
        self.reminder = reminder
        self.phone_number = phone_number
        self.delta = delta
        self.time = time
        self.timezone = timezone

    def __repr__(self):
        return '<Appointment %r>' % self.name

    def get_notification_time(self):
        appointment_time = arrow.get(self.time)
        reminder_time = appointment_time.replace(minutes=-self.delta)
        return reminder_time

