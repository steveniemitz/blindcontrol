import json
import logging

from authlib.flask.oauth2 import current_token
from flask import Blueprint, request
from src.auth.oauth2 import get_user_for_token, require_oauth

from .discovery import Device, DeviceDiscovery
from .frame_constants import DataKeys
from .frames import CommandFrame, FrameData, FrameType, Header, MotoCmd
from .gizapi import GizApi, GizToken

LOG = logging.getLogger(__name__)


class GoogleHome:

  def __init__(self, api: GizApi):
    self._api = api
    self.bp = Blueprint(__name__, 'home')
    self.bp.add_url_rule(
        '/googlehome',
        '_handle_request',
        self._handle_request,
        methods=['POST'])

  @require_oauth()
  def _handle_request(self):
    user = get_user_for_token(current_token.access_token)
    giz_token = GizToken(user.gizToken, user.gizUid, user.gizExpireAt,
                         user.username, user.password)
    js = request.get_json(force=True)
    request_id = js['requestId']
    only_input = js['inputs'][0]
    intent = only_input['intent']
    LOG.info(json.dumps(js))
    if intent == 'action.devices.SYNC':
      return self._handle_sync(request_id, giz_token)
    elif intent == 'action.devices.EXECUTE':
      return self._handle_execute(request_id, only_input['payload'], giz_token)
    elif intent == 'action.devices.QUERY':
      return self._handle_query(request_id, only_input['payload'], giz_token)

  @staticmethod
  def _make_device(dev: Device):
    return {
        'id': '%s#%s' % (dev.did, dev.channel.hex()),
        'type': 'action.devices.types.BLINDS',
        'traits': ['action.devices.traits.OpenClose'],
        'name': {
            'name': dev.name
        },
        'attributes': {
            'openDirection': ['UP']
        },
        'willReportState': True,
        'customData': {
            'did': dev.did,
            'channelHex': dev.channel.hex()
        }
    }

  def _handle_sync(self, request_id, giz_token: GizToken):
    discovery = DeviceDiscovery(self._api, giz_token)
    devices = discovery.discover()
    return json.dumps({
        'requestId': request_id,
        'payload': {
            'agentUserId': giz_token.username,
            'devices': [self._make_device(d) for d in devices]
        }
    })

  def _handle_execute(self, request_id, payload, giz_token):
    commands = payload['commands']
    result_devices = []
    result_pct = 0
    for c in commands:
      for d in c['devices']:
        dev_id = d['id']
        data = d['customData']
        did = data['did']
        channel = bytes.fromhex(data['channelHex'])

        result_devices.append(dev_id)
        for e in c['execution']:
          cmd = e['command']
          assert cmd == 'action.devices.commands.OpenClose'
          pct = e['params']['openPercent']
          frame = CommandFrame(
              header=Header(0, 144, 5),
              frame_type=FrameType.DEVICE_EXECUTE_REQ,
              data=[
                  FrameData(DataKeys.DEVICE_CMD.value,
                            MotoCmd.PERCENT_RUNING_LIGHT_DIMMER.value),
                  FrameData(DataKeys.DEVICE_ADDR_CHANNEL.value, channel),
                  FrameData(DataKeys.DEVICE_CMD_DATA.value,
                            bytes([1, 100 - pct, 0]))
              ])
          self._api.control(giz_token, did, frame)
          result_pct = pct

    return json.dumps({
        'requestId': request_id,
        'payload': {
            'commands': [{
                'ids': result_devices,
                'status': 'SUCCESS',
                'states': {
                    "openPercent": result_pct,
                    "online": True
                }
            }]
        }
    })

  def _handle_query(self, request_id, payload, giz_token):
    ret = {}
    for d in payload['devices']:
      device_id = d['id']
      ret[device_id] = {'online': True}
    return json.dumps({'requestId': request_id, 'payload': {'devices': ret}})
