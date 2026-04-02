import logging
import sys
from . import config

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG if config.DEBUG_LOGGING else logging.INFO
)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


def create_app():
    from .app import create_flask_app
    return create_flask_app()


app = None


def get_app():
    global app
    if app is None:
        app = create_app()
    return app


def main():
    flask_app = create_app()
    flask_app.run()
