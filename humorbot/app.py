import logging
import re
import os

from flask import Flask, request, render_template, send_from_directory
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings

from . import config
from .bot import Humorbot

log = logging.getLogger()


def _build_installation_stores():
    """Build installation and state stores based on available config."""
    if config.DATABASE_URL:
        from sqlalchemy import create_engine
        from slack_sdk.oauth.installation_store.sqlalchemy import SQLAlchemyInstallationStore
        from slack_sdk.oauth.state_store.sqlalchemy import SQLAlchemyOAuthStateStore

        # Heroku uses postgres:// but SQLAlchemy 2.x requires postgresql://
        db_url = config.DATABASE_URL
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)

        engine = create_engine(db_url)
        installation_store = SQLAlchemyInstallationStore(
            client_id=config.SLACK_CLIENT_ID,
            engine=engine,
        )
        state_store = SQLAlchemyOAuthStateStore(
            expiration_seconds=600,
            engine=engine,
        )
        installation_store.create_tables()
        state_store.create_tables()
        return installation_store, state_store
    else:
        from slack_sdk.oauth.installation_store import FileInstallationStore
        from slack_sdk.oauth.state_store import FileOAuthStateStore
        return (
            FileInstallationStore(base_dir='./data/installations'),
            FileOAuthStateStore(expiration_seconds=600, base_dir='./data/states'),
        )


def create_bolt_app():
    if config.SLACK_BOT_TOKEN:
        bolt_app = App(
            token=config.SLACK_BOT_TOKEN,
            signing_secret=config.SLACK_SIGNING_SECRET,
        )
    else:
        installation_store, state_store = _build_installation_stores()
        bolt_app = App(
            signing_secret=config.SLACK_SIGNING_SECRET,
            oauth_settings=OAuthSettings(
                client_id=config.SLACK_CLIENT_ID,
                client_secret=config.SLACK_CLIENT_SECRET,
                scopes=['commands'],
                installation_store=installation_store,
                state_store=state_store,
                install_path='/slack/install',
                redirect_uri_path='/slack/oauth_redirect',
            ),
        )

    hb = Humorbot()

    # --- Command handlers ---

    @bolt_app.command('/frink')
    @bolt_app.command('/morbo')
    def handle_command(ack, command, respond):
        ack()
        try:
            cmd_name = command['command'].replace('/', '').strip()
            res = hb.process_command(cmd_name, command)
            respond(res)
        except Exception as e:
            log.exception('Exception processing command: {}'.format(e))
            respond({'text': 'Error processing request.', 'response_type': 'ephemeral'})

    # --- Action handlers ---

    @bolt_app.action('send_image')
    def handle_send(ack, body, respond):
        ack()
        try:
            res = hb.send(body)
            respond(res)
        except Exception as e:
            log.exception('Exception processing send action: {}'.format(e))
            respond({'text': 'Error processing action.', 'response_type': 'ephemeral'})

    @bolt_app.action('cancel')
    def handle_cancel(ack, body, respond):
        ack()
        respond({'delete_original': True})

    @bolt_app.action('edit_gif')
    def handle_edit_gif(ack, body, respond):
        ack()
        try:
            res = hb.update_gif(body)
            respond(res)
        except Exception as e:
            log.exception('Exception processing edit action: {}'.format(e))
            respond({'text': 'Error processing action.', 'response_type': 'ephemeral'})

    @bolt_app.action('toggle_text')
    def handle_toggle_text(ack, body, respond):
        ack()
        try:
            res = hb.update_gif(body)
            respond(res)
        except Exception as e:
            log.exception('Exception processing toggle action: {}'.format(e))
            respond({'text': 'Error processing action.', 'response_type': 'ephemeral'})

    @bolt_app.action(re.compile(r'set_start_\d+'))
    def handle_set_start(ack, body, respond):
        ack()
        try:
            res = hb.update_gif(body)
            respond(res)
        except Exception as e:
            log.exception('Exception processing set_start action: {}'.format(e))
            respond({'text': 'Error processing action.', 'response_type': 'ephemeral'})

    @bolt_app.action(re.compile(r'set_end_\d+'))
    def handle_set_end(ack, body, respond):
        ack()
        try:
            res = hb.update_gif(body)
            respond(res)
        except Exception as e:
            log.exception('Exception processing set_end action: {}'.format(e))
            respond({'text': 'Error processing action.', 'response_type': 'ephemeral'})

    return bolt_app


def create_flask_app():
    bolt_app = create_bolt_app()
    bolt_handler = SlackRequestHandler(bolt_app)
    flask_app = Flask(__name__)

    # --- Flask routes for Bolt ---

    @flask_app.route('/slack/events', methods=['POST'])
    def slack_events():
        return bolt_handler.handle(request)

    @flask_app.route('/slack/install', methods=['GET'])
    def slack_install():
        return bolt_handler.handle(request)

    @flask_app.route('/slack/oauth_redirect', methods=['GET'])
    def slack_oauth_redirect():
        return bolt_handler.handle(request)

    # --- Flask web routes ---

    @flask_app.route('/')
    def index():
        return render_template(
            'index.html',
            client_id=config.SLACK_CLIENT_ID,
            installed=request.args.get('installed'),
        )

    @flask_app.route('/favicon.ico')
    def favicon():
        return send_from_directory(
            os.path.join(flask_app.root_path, 'static'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon',
        )

    @flask_app.route('/privacy')
    def privacy():
        return render_template('privacy.html')

    @flask_app.route('/usage')
    def usage():
        return render_template('usage.html')

    return flask_app
