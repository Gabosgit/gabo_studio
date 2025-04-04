
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# database connection string postgresql
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Gabo_p@localhost:5432/postgres"
#SQLALCHEMY_DATABASE_URL = os.getenv("local_postgresql_url")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
