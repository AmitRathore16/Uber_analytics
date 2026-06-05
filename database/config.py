import os

# Manual .env parser — reads from root .env (one directory above database/)
def load_dotenv():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_dotenv()

MYSQL_HOST     = os.environ["MYSQL_HOST"]
MYSQL_USER     = os.environ["MYSQL_USER"]
MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
DATABASE_NAME  = os.environ["DATABASE_NAME"]