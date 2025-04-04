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
# Now you can access environment variables using os.getenv()
local_postgresql_url = os.getenv('local_postgresql_url')
my_env = os.environ.copy()  # Create a copy of the current environment

if len(sys.argv) < 2:
    print("Usage: python run_alembic.py <command> [message|revision]")
    sys.exit(1)

command = sys.argv[1]

if command == "revision":
    if len(sys.argv) < 3:
        print("Usage: python run_alembic.py revision <message>")
        sys.exit(1)
    message = sys.argv[2]
    subprocess.run(["alembic", "revision", "--autogenerate", "-m", message], env=my_env)

elif command == "upgrade":
    subprocess.run(["alembic", "upgrade", "head"], env=my_env)

elif command == "downgrade":
    if len(sys.argv) < 3:
        print("Usage: python run_alembic.py downgrade <revision>")
        sys.exit(1)
    revision = sys.argv[2]
    subprocess.run(["alembic", "downgrade", revision], env=my_env)

else:
    print(f"Unknown command: {command}")
    sys.exit(1)