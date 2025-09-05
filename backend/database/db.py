from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL, USER_DATABASE_URL

# Database for predefined structure and data
engine1 = create_engine(DATABASE_URL)
SessionLocal1 = sessionmaker(autocommit=False, autoflush=False, bind=engine1)
Base1 = declarative_base()

def get_db1():
    db = SessionLocal1()
    try:
        yield db
    finally:
        db.close()

# Database for user data, chat, and messages
engine2 = create_engine(USER_DATABASE_URL)
SessionLocal2 = sessionmaker(autocommit=False, autoflush=False, bind=engine2)
Base2 = declarative_base()

def get_db2():
    db = SessionLocal2()
    try:
        yield db
    finally:
        db.close()
