import base64

from cryptography.fernet import Fernet
from google.cloud import kms

from ..config import CONFIG


class _Crypto:
  _ENCRYPTED_KEY = None
  _KMS_KEY_PATH = None

  def _ensure_init(self):
    if self._fernet is None:
      kms_client = kms.KeyManagementServiceClient()
      fernet_key = kms_client.decrypt(self._KMS_KEY_PATH,
                                      base64.b64decode(self._ENCRYPTED_KEY))
      self._key = fernet_key.plaintext
      self._fernet = Fernet(self._key.decode('utf-8'))

  def __init__(self):
    self._key = None
    self._fernet = None

  @property
  def key(self):
    self._ensure_init()
    return self._key

  def encrypt(self, data):
    self._ensure_init()
    return self._fernet.encrypt(data)

  def decrypt(self, encrypted_data):
    self._ensure_init()
    return self._fernet.decrypt(encrypted_data)


class SessionCrypto(_Crypto):
  _ENCRYPTED_KEY = bytes(CONFIG['keys']['session_key']['material'], 'utf-8')
  _KMS_KEY_PATH = CONFIG['keys']['session_key']['path']


SESSION = SessionCrypto()


class PasswordCrypto(_Crypto):
  _ENCRYPTED_KEY = bytes(CONFIG['keys']['password_key']['material'], 'utf-8')
  _KMS_KEY_PATH = CONFIG['keys']['password_key']['path']


PASSWORD = PasswordCrypto()
