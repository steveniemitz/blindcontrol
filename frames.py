import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import List

from binary_reader import BinaryReader
from binary_writer import BinaryWriter
from frame_constants import DATAKEYS_BY_ID, DataKey, DataKeyType


class MotoCmd(Enum):
  UP = 16
  DOWN = 18
  PERCENT_RUNING_LIGHT_DIMMER = 25


@dataclass
class FrameData:
  key: DataKey
  value: any


@dataclass
class Header:
  flag: int
  cmd: int
  action: int


@dataclass
class CommandFrame:
  header: Header
  frame_type: int
  seq_num: int = 0
  data: List[FrameData] = field(default_factory=list)


class FrameType:
  ROOM_LIST_REQ = 256
  DEVICE_LIST_REQ = 288
  DEVICE_LIST_RESP = 289
  DEVICE_EXECUTE_REQ = 290
  DEVICE_STATUS_RESP = 291
  DEVICE_PARA_REQ = 298
  DEVICE_PARA_RESP = 299
  DEVICE_RSSI_REQ = 300


class FrameDecoder:

  def _decode_header(self, reader):
    reader.get_int()  # version number?
    total_len = reader.get_varint()
    flag = reader.get()
    cmd = reader.get_short()
    action = None
    if cmd == 145 and total_len > 3:
      action = reader.get()

    return total_len - 3, Header(flag, cmd, action)

  def _decode_body(self, reader):
    reader.set_order('<')
    frame_start_mark = reader.get_bytes(12)
    if frame_start_mark != FrameEncoder._FRAME_START:
      raise ValueError('invalid message')
    body_len = reader.get_short()
    frame_type = reader.get_short()
    frame_num = reader.get_short()
    reserved = reader.get_bytes(6)

    read = 2 + 2 + 6
    data = []
    while read < body_len - 2:
      data_key_id = reader.get_short()
      data_key = DATAKEYS_BY_ID.get(data_key_id)
      value_len = reader.get_short()
      if not data_key:
        reader.get_bytes(value_len)
      else:
        data_key_type = data_key.key_type
        data_value = None
        read += 4
        if data_key_type in (DataKeyType.BYTE, DataKeyType.UINT8):
          data_value = reader.get()
        elif data_key_type == DataKeyType.STRING:
          data_value = reader.get_bytes(value_len).decode('utf-8')
        elif data_key_type == DataKeyType.BYTES:
          data_value = reader.get_bytes(value_len)
        elif data_key_type == DataKeyType.UINT16:
          data_value = reader.get_short()
        elif data_key_type == DataKeyType.UINT32:
          data_value = reader.get_int()
        data.append(FrameData(data_key, data_value))

      read += value_len

    return frame_type, frame_num, data

  def decode(self, data: bytes):
    reader = BinaryReader(data, '>')
    total_len, header = self._decode_header(reader)
    frame_type = None
    seq_num = None
    data = None
    if total_len > 0:
      frame_type, seq_num, data = self._decode_body(reader)
    return CommandFrame(
        header=header, frame_type=frame_type, seq_num=seq_num, data=data)


class FrameEncoder:
  _FRAME_START = bytes([83, 109, 97, 114, 116, 95, 73, 100, 49, 95, 121, 58])
  _FRAME_END = 0xFF
  _RESERVED = bytes([0, 0, 0, 0, 0, 0])

  def __init__(self):
    self._seq = 3

  @staticmethod
  def _checksum(data: bytes, start: int, end: int):
    i = start
    acc = 0
    while i < end:
      acc += data[i] & 0xFF
      i += 1
    return acc % 256

  def _encode_header(self, frame: CommandFrame, body_len: int):
    header = BinaryWriter(bytearray(), '>')
    total_len = body_len + 1 + 2 + (1 if frame.header.action is not None else 0)
    header.put_int(0x03)
    header.put_varint(total_len)
    header.put(frame.header.flag)
    header.put_short(frame.header.cmd)
    if frame.header.action is not None:
      header.put(frame.header.action)
    return header.to_bytes()

  def _encode_body(self, frame: CommandFrame):
    body = BinaryWriter(bytearray(), '<')
    body.put_short(frame.frame_type & 0xFFFF)
    body.put_short(self._seq & 0xFFFF)
    body.put_bytes(self._RESERVED)

    for d in frame.data:
      body.put_short(d.key.key_id)
      if d.key.key_type == DataKeyType.BYTES:
        body.put_short(len(d.value))
        body.put_bytes(d.value)
      elif d.key.key_type == DataKeyType.BYTE:
        body.put_short(1)
        body.put(d.value)
      else:
        raise ValueError('unknown value type')

    body.put(self._FRAME_END)
    chk = self._checksum(body.to_bytes(), 0, len(body))
    body.put(chk)
    len_bytes = struct.pack('<H', len(body))
    return self._FRAME_START + len_bytes + body.to_bytes()

  def encode(self, frame: CommandFrame):
    self._seq += 1
    body = self._encode_body(frame)
    header = self._encode_header(frame, len(body))
    return header + body


DEFAULT_ENCODER = FrameEncoder()
DEFAULT_DECODER = FrameDecoder()
