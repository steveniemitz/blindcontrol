import time
import urllib.parse

from authlib.flask.oauth2 import AuthorizationServer, ResourceProtector
from authlib.specs.rfc6749 import OAuth2Error, grants
from authlib.specs.rfc6750 import BearerTokenValidator
from flask import (Blueprint, make_response, redirect, render_template, request,
                   session)
from werkzeug.security import gen_salt

from ..config import CONFIG
from ..gizapi import GizApi, GizAuthError, GizToken
from .datastore import AuthCodeRepo, TokenRepo, UserRepo
from .models import OAuth2AuthorizationCode, OAuth2Client, User

CLIENTS = {
    client_name: OAuth2Client(
        client_id=client_name,
        client_secret=cc['client_secret'],
        redirect_uris=cc['allowed_urls'])
    for client_name, cc in CONFIG['oauth_clients'].items()
}


class AuthorizationCodeGrant(grants.AuthorizationCodeGrant):

  def create_authorization_code(self, client, user, request):
    code = gen_salt(48)
    item = OAuth2AuthorizationCode(
        code=code,
        client_id=client.client_id,
        redirect_uri=request.redirect_uri,
        scope=request.scope,
        user_id=user.username,
        auth_time=int(time.time()),
        response_type='code')
    AuthCodeRepo.put_auth_code(item)
    return code

  def parse_authorization_code(self, code, client):
    item = AuthCodeRepo.get_auth_code(code)
    if item and not item.is_expired() and item.client_id == client.client_id:
      return item

  def delete_authorization_code(self, authorization_code):
    AuthCodeRepo.del_auth_code(authorization_code.code)

  def authenticate_user(self, authorization_code):
    grant = AuthCodeRepo.get_auth_code(authorization_code.code)
    return UserRepo.get_user(grant.user_id)


class RefreshTokenGrant(grants.RefreshTokenGrant):

  def authenticate_refresh_token(self, refresh_token):
    item = TokenRepo.get_token_by_refresh_token(refresh_token)
    if item and not item.is_refresh_token_expired():
      return item

  def authenticate_user(self, credential):
    return UserRepo.get_user(credential.user_id)


def query_client(client_id):
  return CLIENTS[client_id]


def save_token(token, request):
  TokenRepo.put_token(token, request)


def _update_user(new_token: GizToken):
  username = new_token.username
  user = UserRepo.get_user(username)
  user.gizToken = new_token.token
  user.gizUid = new_token.uid
  user.gizExpireAt = new_token.expire_at
  UserRepo.put_user(user)


GizApi.register_hook(_update_user)

authorization = AuthorizationServer(
    query_client=query_client,
    save_token=save_token,
)


class _BearerTokenValidator(BearerTokenValidator):

  def request_invalid(self, request):
    return False

  def token_revoked(self, token):
    return False

  def authenticate_token(self, token_string):
    return TokenRepo.get_token(token_string)

  def scope_insufficient(self, token, scope, operator='AND'):
    return False


class OAuth:

  def __init__(self, api: GizApi):
    self._api = api
    self.bp = Blueprint(__name__, 'oauth')
    self.bp.add_url_rule('/oauth/login', 'login', self.login, methods=['POST'])
    self.bp.add_url_rule(
        '/oauth/login', 'show_login', self.show_login, methods=['GET'])
    self.bp.add_url_rule(
        '/oauth/authorize',
        'authorize',
        self.authorize,
        methods=['GET', 'POST'])
    self.bp.add_url_rule(
        '/oauth/token', 'token', self.issue_token, methods=['POST'])

  def show_login(self):
    return render_template('login.html')

  def login(self):
    username = request.form['username']
    password = request.form['password']
    dst = request.args.get('return')
    try:
      login_result = self._api.login(username, password)
      user = User(
          username=username,
          password=password,
          gizToken=login_result.token,
          gizUid=login_result.uid,
          gizExpireAt=login_result.expire_at)
    except GizAuthError as e:
      return render_template('login.html', errormessage=e)

    UserRepo.put_user(user)
    session['username'] = username
    resp = redirect(dst) if dst else make_response()
    return resp

  def authorize(self):

    def _make_redirect():
      return redirect('/oauth/login?return=%s' %
                      urllib.parse.quote(request.url))

    username = session.get('username')
    if not username:
      return _make_redirect()

    user = User(username, None)
    if user:
      return authorization.create_authorization_response(grant_user=user)

  def issue_token(self):
    return authorization.create_token_response()


_token_validator = _BearerTokenValidator()

require_oauth = ResourceProtector()
require_oauth.register_token_validator(_token_validator)


def get_user_for_token(token) -> User:
  token = _token_validator(token, None, None)
  u = UserRepo.get_user(token.user_id)
  if not u:
    raise OAuth2Error('user not found for token')
  return u


def config_oauth(app):
  authorization.init_app(app)
  authorization.register_grant(AuthorizationCodeGrant)
  authorization.register_grant(RefreshTokenGrant)
