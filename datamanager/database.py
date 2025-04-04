import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

load_dotenv()

# Check for Render.com's DATABASE_URL first
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # Use Render.com's DATABASE_URL
    SQLALCHEMY_DATABASE_URL = DATABASE_URL
else:
    # Use .env variables if DATABASE_URL is not set
    # database connection string postgresql
    SERVER_PWD = os.getenv('SERVER_PWD') # to get a string like this run: openssl rand -hex 32
    DATABASE_HOST = os.getenv("DATABASE_HOST")
    DATABASE_PORT = os.getenv("DATABASE_PORT")
    DATABASE_NAME = os.getenv("DATABASE_NAME")
    DATABASE_USER = os.getenv("DATABASE_USER")
    DATABASE_DRIVER = os.getenv("DATABASE_DRIVER")
    SQLALCHEMY_DATABASE_URL = f"{DATABASE_DRIVER}://{DATABASE_USER}:{SERVER_PWD}@{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"


engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
