import struct


class BinaryReader:

  def __init__(self, data: bytes, order: str = '>'):
    self._d = data
    self._pos = 0
    self._order = order

  def set_order(self, new_order: str):
    self._order = new_order

  def get(self):
    ret = self._d[self._pos]
    self._pos += 1
    return ret

  def peek(self):
    return self._d[self._pos]

  def get_short(self):
    ret = struct.unpack_from('%sH' % self._order, self._d, self._pos)
    self._pos += 2
    return ret[0]

  def get_int(self):
    ret = struct.unpack_from('%sI' % self._order, self._d, self._pos)
    self._pos += 4
    return ret[0]

  def get_bytes(self, num):
    ret = self._d[self._pos:self._pos + num]
    self._pos += num
    return ret

  def get_varint(self):
    acc = 0
    shift = 0
    while True:
      b = self.get()
      acc |= ((b & 0x7f) << shift)
      shift += 7
      if b & 0x80 == 0:
        return acc
