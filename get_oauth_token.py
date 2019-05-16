from oauth2client.client import OAuth2WebServerFlow

from config import CONFIG

# Copy your credentials from the APIs Console
CLIENT_ID = 'google-home'
CLIENT_SECRET = CONFIG['oauth_clients'][CLIENT_ID]['client_secret']

# Redirect URI for installed apps
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Run through the OAuth flow and retrieve credentials
flow = OAuth2WebServerFlow(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    scope='test',
    redirect_uri=REDIRECT_URI,
    auth_uri='http://localhost:8080/oauth/auth',
    token_uri='http://localhost:8080/oauth/token')

authorize_url = flow.step1_get_authorize_url()
print('Go to the following link in your browser: ' + authorize_url)
code = input('Enter verification code: ').strip()
credentials = flow.step2_exchange(code)

print(credentials.access_token)
