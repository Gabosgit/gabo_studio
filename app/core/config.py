import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256') #HS256 for Local Functionality
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 30))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set.")
if not ALGORITHM:
    raise ValueError("ALGORITHM environment variable not set.")