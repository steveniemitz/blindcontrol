import time
from dataclasses import dataclass

import requests

from config import CONFIG
from frames import DEFAULT_ENCODER, CommandFrame, FrameEncoder
from js import JSON

_DEFAULT_APPID = CONFIG['appid']
_ROOT_URL = 'https://usapi.gizwits.com/app/'


@dataclass
class GizToken:
  token: str
  uid: str
  expire_at: int
  username: str
  password: str


@dataclass
class Binding:
  did: str


class GizAuthError(Exception):
  pass


class GizApi:
  _TOKEN_UPDATE_HOOKS = []

  @classmethod
  def register_hook(cls, hook):
    cls._TOKEN_UPDATE_HOOKS.append(hook)

  def __init__(self,
               root=_ROOT_URL,
               appid=_DEFAULT_APPID,
               enc: FrameEncoder = None):
    self._appid = appid
    self._root = root
    self._session = requests.session()
    self._enc = enc or DEFAULT_ENCODER

  @property
  def appid(self):
    return self._appid

  def _make_url(self, suffix):
    return '%s%s' % (self._root, suffix)

  def check_token(self, token: GizToken):
    if not token:
      return None
    if token.expire_at <= int(time.time()):
      new_token = self.login(token.username, token.password)
      for h in self._TOKEN_UPDATE_HOOKS:
        h(new_token)
      return new_token
    else:
      return token

  def _post(self, suffix, json_obj, token: GizToken = None):
    token = self.check_token(token)
    headers = {
        'X-Gizwits-Application-Id': self._appid,
        'Content-Type': 'application/json'
    }
    if token:
      headers['X-Gizwits-User-token'] = token.token
    data = JSON.dumps(json_obj)
    return self._session.post(
        self._make_url(suffix), data=data, headers=headers).json()

  def _get(self, suffix, token: GizToken = None):
    token = self.check_token(token)
    headers = {'X-Gizwits-Application-Id': self._appid}
    if token:
      headers['X-Gizwits-User-token'] = token.token

    return self._session.get(self._make_url(suffix), headers=headers).json()

  def login(self, username: str, password: str):
    resp = self._post(
        'login', json_obj={
            'username': username,
            'password': password
        })
    if 'error_message' in resp:
      raise GizAuthError(resp['error_message'])
    return GizToken(username=username, password=password, **resp)

  def list_bindings(self, giz_token: GizToken):
    resp = self._get('bindings', giz_token)
    devices = resp['devices']
    return [Binding(d['did']) for d in devices]

  def control(self, giz_token: GizToken, did: str, frame: CommandFrame):
    msg = {"raw": self._enc.encode(frame)}
    return self._post('control/%s' % did, msg, giz_token)
