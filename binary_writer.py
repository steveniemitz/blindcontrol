import struct


class BinaryWriter:

  def __init__(self, strm: bytearray, order='>'):
    self._strm = strm
    self._pos = 0
    self._endian = order

  def _check_buf(self, needed):
    if self._pos + needed > len(self._strm):
      resize = max(100, needed)
      self._strm.extend(bytes(resize))

  def put(self, value: int):
    self._check_buf(1)
    struct.pack_into('%sB' % self._endian, self._strm, self._pos, value)
    self._pos += 1

  def put_short(self, value: int):
    self._check_buf(2)
    struct.pack_into('%sH' % self._endian, self._strm, self._pos, value)
    self._pos += 2

  def put_int(self, value: int):
    self._check_buf(4)
    struct.pack_into('%sI' % self._endian, self._strm, self._pos, value)
    self._pos += 4

  def put_bytes(self, value: bytes):
    vlen = len(value)
    self._check_buf(vlen)
    self._strm[self._pos:self._pos + vlen] = value
    self._pos += vlen

  def put_varint(self, value: int):
    while True:
      towrite = value & 0x7f
      value >>= 7
      if value:
        self.put(towrite | 0x80)
      else:
        self.put(towrite)
        break

  def to_bytes(self):
    return bytes(self._strm[0:self._pos])

  def __len__(self):
    return self._pos
