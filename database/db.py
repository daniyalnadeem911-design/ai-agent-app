from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime
import os

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    google_id = Column(String(100), unique=True, nullable=False)
    email = Column(String(200), nullable=False)
    name = Column(String(200))
    picture = Column(String(500))
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expiry = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EmailCache(Base):
    __tablename__ = 'email_cache'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    gmail_id = Column(String(100), unique=True)
    sender = Column(String(300))
    subject = Column(String(500))
    snippet = Column(Text)
    body = Column(Text)
    summary = Column(Text)
    urgency = Column(String(50))
    category = Column(String(100))
    cached_at = Column(DateTime, default=datetime.datetime.utcnow)


def get_engine():
    os.makedirs('database', exist_ok=True)
    engine = create_engine('sqlite:///database/app.db', echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session():
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()