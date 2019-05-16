import logging

from flask import Flask
from flask.sessions import SecureCookieSessionInterface
from itsdangerous import URLSafeTimedSerializer

from src.alexa import Alexa
from src.auth.oauth2 import OAuth, config_oauth
from src.config import CONFIG
from src.gizapi import GizApi
from src.googlehome import GoogleHome

logging.basicConfig(level='INFO')

if CONFIG.get('enable_debugger', False):
  try:
    import googleclouddebugger
    googleclouddebugger.enable()
  except ImportError:
    pass


class KmsSecureCookieSessionInterface(SecureCookieSessionInterface):

  def get_signing_serializer(self, app):
    from src.auth.crypto import SESSION
    secret_key = SESSION.key
    signer_kwargs = dict(
        key_derivation=self.key_derivation, digest_method=self.digest_method)
    return URLSafeTimedSerializer(
        secret_key,
        salt=self.salt,
        serializer=self.serializer,
        signer_kwargs=signer_kwargs)


app = Flask(__name__)
app.config.update({'OAUTH2_REFRESH_TOKEN_GENERATOR': True})
app.session_interface = KmsSecureCookieSessionInterface()

api = GizApi()
alexa = Alexa(api)
oauth = OAuth(api)
gh = GoogleHome(api)

config_oauth(app)
app.register_blueprint(oauth.bp, url_prefix='')
app.register_blueprint(alexa.bp, url_prefix='')
app.register_blueprint(gh.bp, uri_prefix='')


@app.route('/ping')
def ping():
  return 'pong'


if __name__ == '__main__':
  # This is used when running locally only. When deploying to Google App
  # Engine, a webserver process such as Gunicorn will serve the app. This
  # can be configured by adding an `entrypoint` to app.yaml.
  app.run(host='127.0.0.1', port=8080, debug=True)
