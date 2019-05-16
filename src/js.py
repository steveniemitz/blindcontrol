import json


class _BytesJSONEncoder(json.JSONEncoder):

  def default(self, o):
    if isinstance(o, bytes) or isinstance(o, bytearray):
      return [int(b & 0xFF) for b in o]
    else:
      return super(_BytesJSONEncoder, self).default(o)


class JSON:

  @staticmethod
  def dumps(obj):
    return json.dumps(obj, cls=_BytesJSONEncoder)

  @staticmethod
  def loads(value):
    return json.loads(value)
