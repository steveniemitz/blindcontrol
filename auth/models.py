from dataclasses import dataclass, field
from authlib.oauth2.rfc6749.models import ClientMixin, TokenMixin
from typing import List
import time

@dataclass
class User:
  username: str
  password: str
  gizToken: str = None
  gizUid: str = None
  gizExpireAt: int = -1

@dataclass
class Session:
  session_id: str
  user_id: str
  expires_at: int

@dataclass
class OAuth2Client(ClientMixin):
  client_id: str
  client_secret: str
  redirect_uris: List[str]

  grant_types: List[str] = field(default_factory=lambda: ['authorization_code'])
  response_types: List[str] = field(default_factory=lambda: ['code'])

  def __repr__(self):
    return '<Client: {}>'.format(self.client_id)

  def get_client_id(self):
    return self.client_id

  def get_default_redirect_uri(self):
    if self.redirect_uris:
      return self.redirect_uris[0]

  def check_redirect_uri(self, redirect_uri):
    return redirect_uri in self.redirect_uris

  def has_client_secret(self):
    return bool(self.client_secret)

  def check_client_secret(self, client_secret):
    return self.client_secret == client_secret

  def check_token_endpoint_auth_method(self, method):
    return True

  def check_response_type(self, response_type):
    if self.response_types:
      return response_type in self.response_types
    return False

  def check_grant_type(self, grant_type):
    if self.grant_types:
      return grant_type in self.grant_types
    return False

  def check_requested_scopes(self, scopes):
    return True


@dataclass
class OAuth2AuthorizationCode:
  code: str
  client_id: str
  redirect_uri: str
  response_type: str
  scope: str
  auth_time: int
  user_id: str

  def is_expired(self):
    return self.auth_time + 300 < time.time()

  def get_redirect_uri(self):
    return self.redirect_uri

  def get_scope(self):
    return self.scope

  def get_auth_time(self):
    return self.auth_time

@dataclass
class OAuth2Token(TokenMixin):
  access_token: str
  token_type: str
  scope: str
  expires_at: int
  user_id: str

  def get_scope(self):
    return self.scope

  def get_expires_at(self):
    return self.expires_at

  def get_expires_in(self):
    return self.expires_at - int(time.time())

  def is_expired(self):
    return self.get_expires_in() < 0

@dataclass
class OAuth2RefreshToken:
  refresh_token: str
  access_token: str