import os
import json
import tempfile
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import Config

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

_flow_store = {}


def create_flow():
    client_secret_json = os.getenv('GOOGLE_CLIENT_SECRET_JSON')

    if client_secret_json:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(client_secret_json)
            tmp_path = f.name
        flow = Flow.from_client_secrets_file(
            tmp_path,
            scopes=Config.GOOGLE_SCOPES,
            redirect_uri=Config.REDIRECT_URI
        )
        os.unlink(tmp_path)
    else:
        flow = Flow.from_client_secrets_file(
            Config.CLIENT_SECRETS_FILE,
            scopes=Config.GOOGLE_SCOPES,
            redirect_uri=Config.REDIRECT_URI
        )
    return flow


def get_authorization_url():
    flow = create_flow()
    auth_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    _flow_store[state] = flow
    return auth_url, state


def exchange_code_for_tokens(authorization_response_url, state):
    flow = _flow_store.pop(state, None)
    if not flow:
        flow = create_flow()
    flow.fetch_token(authorization_response=authorization_response_url)
    return flow.credentials


def credentials_to_dict(credentials):
    return {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes
    }


def dict_to_credentials(credentials_dict):
    return Credentials(
        token=credentials_dict['token'],
        refresh_token=credentials_dict.get('refresh_token'),
        token_uri=credentials_dict['token_uri'],
        client_id=credentials_dict['client_id'],
        client_secret=credentials_dict['client_secret'],
        scopes=credentials_dict['scopes']
    )


def get_user_info(credentials):
    service = build('oauth2', 'v2', credentials=credentials)
    return service.userinfo().get().execute()


def refresh_credentials_if_needed(credentials):
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())
    return credentials