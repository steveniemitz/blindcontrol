import asyncio
import logging
from dataclasses import dataclass
from typing import List

import websockets

from frame_constants import DataKeys
from frames import (DEFAULT_DECODER, DEFAULT_ENCODER, CommandFrame, FrameData,
                    FrameDecoder, FrameEncoder, FrameType, Header)
from gizapi import GizApi, GizToken
from js import JSON

LOG = logging.getLogger('discovery')


@dataclass
class Device:
  did: str
  channel: bytes
  name: str
  closed_pct: int


_LOOP = asyncio.get_event_loop()


class DeviceDiscovery:

  def __init__(self,
               api: GizApi,
               token: GizToken,
               enc: FrameEncoder = None,
               dec: FrameDecoder = None,
               url: str = 'wss://ussandbox.gizwits.com:8880/ws/app/v1'):
    self._url = url
    self._token = token
    self._api = api
    self._enc = enc or DEFAULT_ENCODER
    self._dec = dec or DEFAULT_DECODER

  def _login_msg(self, token):
    return JSON.dumps({
        "cmd": "login_req",
        "data": {
            "appid": self._api.appid,
            "uid": token.uid,
            "token": token.token,
            "p0_type": "custom",
            "heartbeat_interval": 180,
            "auto_subscribe": True
        }
    })

  async def _send(self, ws, did: str, frame: CommandFrame):
    await ws.send(
        JSON.dumps({
            "cmd": "c2s_raw",
            "data": {
                "did": did,
                "raw": self._enc.encode(frame)
            }
        }))

  async def _list_devices(self, ws, did):
    msg = CommandFrame(
        header=Header(0, 144, 5), frame_type=FrameType.DEVICE_LIST_REQ)
    await self._send(ws, did, msg)

    while True:
      resp = await ws.recv()
      js = JSON.loads(resp)
      resp_did = js['data']['did']
      if did == resp_did:
        frame_data = bytes(js['data']['raw'])
        decoded_frame = self._dec.decode(frame_data)
        if decoded_frame.frame_type == FrameType.DEVICE_LIST_RESP:
          return decoded_frame
        else:
          LOG.debug('ignoring unexpected frame %s' % decoded_frame)
      else:
        LOG.info('ignoring unexected did')

  async def _discover(self):
    token = self._api.check_token(self._token)
    bindings = self._api.list_bindings(token)
    async with websockets.connect(self._url, ssl=True) as ws:
      await ws.send(self._login_msg(token))
      login_resp = await ws.recv()
      devices = [(b.did, await self._list_devices(ws, b.did)) for b in bindings]
      return devices

  async def _query(self, devices: List[Device]):
    token = self._api.check_token(self._token)
    async with websockets.connect(self._url, ssl=True) as ws:
      await ws.send(self._login_msg(token))
      login_resp = await ws.recv()
      devices = [
          Device(d.did, d.channel, d.name, await self._query_device(ws, d))
          for d in devices
      ]
      return devices

  async def _query_device(self, ws, d: Device):
    frame = CommandFrame(
        header=Header(0, 144, 5),
        frame_type=FrameType.DEVICE_PARA_REQ,
        data=[
            FrameData(DataKeys.DEVICE_ADDR_CHANNEL.value, d.channel),
        ])
    await self._send(ws, d.did, frame)
    await ws.recv()
    resp = await ws.recv()
    js = JSON.loads(resp)
    frame_data = bytes(js['data']['raw'])
    decoded = self._dec.decode(frame_data)
    inner_para_data = [
        f for f in decoded.data if f.key == DataKeys.INNER_PARA_DATA.value
    ]
    if inner_para_data:
      return inner_para_data[0].value[0]
    else:
      return None

  def discover(self):
    devices: List[(str,
                   CommandFrame)] = _LOOP.run_until_complete(self._discover())
    ret = []
    for (did, d) in devices:
      channels = [
          c.value for c in d.data if c.key == DataKeys.DEVICE_ADDR_CHANNEL.value
      ]
      names = [c.value for c in d.data if c.key == DataKeys.NAME.value]
      positions = [
          int(c.value[1])
          for c in d.data
          if c.key == DataKeys.DEVICE_CMD_DATA.value
      ]
      ret += [
          Device(did, channel, name, position)
          for (channel, name, position) in zip(channels, names, positions)
      ]
    return ret

  def query(self, devices: List[Device]):
    return _LOOP.run_until_complete(self._query(devices))
