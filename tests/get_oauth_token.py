import os

from google_auth_oauthlib.flow import InstalledAppFlow
from src.config import CONFIG

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

# Copy your credentials from the APIs Console
CLIENT_ID = 'google-home'
CLIENT_SECRET = CONFIG['oauth_clients'][CLIENT_ID]['client_secret']
client_config = {
    'installed': {
        'auth_uri': 'http://localhost:8080/oauth/authorize',
        'token_uri': 'http://localhost:8080/oauth/token',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
}


flow = InstalledAppFlow.from_client_config(client_config, ['test'])
creds = flow.run_local_server(port=8082)

print('token: %s' % creds.token)
