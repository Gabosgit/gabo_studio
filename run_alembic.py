"""
USAGE IN TERMINAL:
python run_alembic.py revision "Message ..."
python run_alembic.py upgrade
python run_alembic.py downgrade <revision_hash> or python run_alembic.py downgrade -1
"""

import os
from dotenv import load_dotenv
import subprocess
import sys

load_dotenv()

SERVER_PWD = os.getenv('SERVER_PWD')
DATABASE_HOST = os.getenv('DATABASE_HOST')
DATABASE_PORT = os.getenv('DATABASE_PORT')
DATABASE_NAME = os.getenv('DATABASE_NAME')

os.environ['SERVER_PWD'] = SERVER_PWD
os.environ['DATABASE_HOST'] = DATABASE_HOST
os.environ['DATABASE_PORT'] = DATABASE_PORT
os.environ['DATABASE_NAME'] = DATABASE_NAME

if len(sys.argv) < 2:
    print("Usage: python run_alembic.py <command> [message|revision]")
    sys.exit(1)

command = sys.argv[1]

if command == "revision":
    if len(sys.argv) < 3:
        print("Usage: python run_alembic.py revision <message>")
        sys.exit(1)
    message = sys.argv[2]
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", message])

elif command == "upgrade":
    subprocess.run(["alembic", "upgrade", "head"])

elif command == "downgrade":
    if len(sys.argv) < 3:
        print("Usage: python run_alembic.py downgrade <revision>")
        sys.exit(1)
    revision = sys.argv[2]
    subprocess.run(["alembic", "downgrade", revision])

else:
    print(f"Unknown command: {command}")
    sys.exit(1)