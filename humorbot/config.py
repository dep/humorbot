import os
from dotenv import load_dotenv

load_dotenv()


def _bool(val):
    return str(val).lower() in ('true', '1', 'yes')


SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET', '')
SLACK_CLIENT_ID = os.environ.get('HUMORBOT_CLIENT_ID', '')
SLACK_CLIENT_SECRET = os.environ.get('HUMORBOT_CLIENT_SECRET', '')
DATABASE_URL = os.environ.get('DATABASE_URL', '')
DEBUG_LOGGING = _bool(os.environ.get('DEBUG_LOGGING', 'false'))
