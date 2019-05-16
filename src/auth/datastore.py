import dataclasses
import time

from google.cloud.datastore import Client, Entity

from ..config import CONFIG
from . import crypto
from .models import (OAuth2AuthorizationCode, OAuth2RefreshToken, OAuth2Token,
                     Session, User)

_CLIENT = None


def CLIENT():
  global _CLIENT
  if _CLIENT is None:
    _CLIENT = Client(project=CONFIG['project'])
  return _CLIENT


class AuthCodeRepo:
  KIND = 'AuthCode'

  @classmethod
  def put_auth_code(cls, code):
    code_key = CLIENT().key(cls.KIND, code.code)
    ent = Entity(code_key)
    ent.update(dataclasses.asdict(code))
    CLIENT().put(ent)

  @classmethod
  def get_auth_code(cls, code):
    code_key = CLIENT().key(cls.KIND, code)
    ent = CLIENT().get(code_key)
    return OAuth2AuthorizationCode(**ent) if ent else None

  @classmethod
  def del_auth_code(cls, code):
    code_key = CLIENT().key(cls.KIND, code)
    CLIENT().delete(code_key)


class TokenRepo:
  KIND = 'GrantToken'
  REFRESH_KIND = 'RefreshToken'

  @classmethod
  def put_token(cls, token, request):
    key = CLIENT().key(cls.KIND, token['access_token'])
    token_obj = OAuth2Token(
        token_type=token['token_type'],
        access_token=token['access_token'],
        scope=token['scope'],
        expires_at=token['expires_in'] + int(time.time()),
        user_id=request.user.username)
    ent = Entity(key)
    ent.update(dataclasses.asdict(token_obj))
    CLIENT().put(ent)

    refresh_token = token['refresh_token']
    refresh_obj = OAuth2RefreshToken(refresh_token, token_obj.access_token)
    key = CLIENT().key(cls.REFRESH_KIND, refresh_token)
    ent = Entity(key)
    ent.update(dataclasses.asdict(refresh_obj))
    CLIENT().put(ent)

  @classmethod
  def get_token(cls, token_string):
    key = CLIENT().key(cls.KIND, token_string)
    ent = CLIENT().get(key)
    return OAuth2Token(**ent) if ent else None

  @classmethod
  def get_token_by_refresh_token(cls, refresh_token):
    key = CLIENT().key(cls.REFRESH_KIND, refresh_token)
    ent = CLIENT().get(key)
    if ent is None:
      return None
    return cls.get_token(ent['access_token'])

  @classmethod
  def del_token(cls, token):
    key = CLIENT().key(cls.KIND, token)
    CLIENT().delete(key)


class UserRepo:
  KIND = 'User'

  @classmethod
  def get_user(cls, user_id) -> User:
    key = CLIENT().key(cls.KIND, user_id)
    ent = CLIENT().get(key)
    encrypted_password = ent.pop('encrypted_password')
    password = crypto.PASSWORD.decrypt(encrypted_password)
    ent['password'] = password.decode('utf-8')
    return User(**ent) if ent else None

  @classmethod
  def put_user(cls, user):
    key = CLIENT().key(cls.KIND, user.username)
    ent = Entity(key)
    user_dct = dataclasses.asdict(user)
    user_dct.pop('password')
    user_dct['encrypted_password'] = crypto.PASSWORD.encrypt(
        user.password.encode('utf-8'))
    ent.update(user_dct)
    CLIENT().put(ent)


class SessionRepo:
  KIND = 'Session'

  @classmethod
  def put_session(cls, username):
    return Session(
        crypto.SESSION.encrypt(username.encode('utf-8')), username, 0)

  @classmethod
  def get_session(cls, session_id):
    decrypted_user_bytes = crypto.SESSION.decrypt(session_id.encode('utf-8'))
    return Session(session_id, decrypted_user_bytes.decode('utf-8'), 0)
