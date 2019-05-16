from flask import Blueprint, request
from auth.oauth2 import get_user_for_token
from gizapi import GizApi, GizToken
from discovery import DeviceDiscovery, Device
from frames import CommandFrame, Header, FrameType, MotoCmd, FrameData, FrameEncoder, DEFAULT_ENCODER
from frame_constants import DataKeys
from uuid import uuid4
import json
from datetime import datetime
import logging

class Capabilities:
  ALEXA = {
    'type': 'AlexaInterface',
    'interface': 'Alexa',
    'version': '3'
  }

  @staticmethod
  def simple(interface_name: str, supported: str):
    return {
      'type': 'AlexaInterface',
      'interface': interface_name,
      'version': '3',
      'properties': {
        'supported': [{'name': supported}],
        'proactivelyReported': True,
        'retrievable': False
      }
    }

LOG = logging.getLogger('alexa')

class Alexa:
  def __init__(self, api: GizApi, enc: FrameEncoder=None):
    self.bp = Blueprint(__name__, 'home')
    self._api = api
    self._enc = enc or DEFAULT_ENCODER
    self.bp.add_url_rule('/alexa/directives', 'handle_request', self.handle_request, methods=['POST'])

  def handle_request(self):
    js = request.get_json(force=True)
    directive = js['directive']
    header = directive['header']
    method = '%s.%s' % (header['namespace'], header['name'])
    if method == 'Alexa.Discovery.Discover':
      return self._handle_discovery(directive)
    elif method == 'Alexa.PowerController.TurnOn':
      return self._handle_on_off(directive, 'ON')
    elif method == 'Alexa.PowerController.TurnOff':
      return self._handle_on_off(directive, 'OFF')
    elif method == 'Alexa.PercentageController.SetPercentage':
      return self._handle_pct(directive)

  @staticmethod
  def _giz_token_from_bearer(token: str):
    user = get_user_for_token(token)
    return GizToken(user.gizToken, user.gizUid, user.gizExpireAt, user.username, user.password)

  def _handle_discovery(self, directive):
    bearer_token = directive['payload']['scope']['token']
    giz_token = self._giz_token_from_bearer(bearer_token)
    discovery = DeviceDiscovery(self._api, giz_token)
    devices = discovery.discover()
    return json.dumps({
      'event': {
        'header': {
          'namespace': 'Alexa.Discovery',
          'name': 'Discover.Response',
          'payloadVersion': '3',
          'messageId': str(uuid4())
        },
        'payload': {
          'endpoints': [self._make_endpoint(ep) for ep in devices]
        }
      }
    })

  @staticmethod
  def _make_endpoint(device: Device):
    return {
      "endpointId": "%s#%s" % (device.did, device.channel.hex()),
      "manufacturerName": "Shade Store",
      "description": "Smart Blind by Shade Store",
      "displayCategories": ["SWITCH"],
      "friendlyName": device.name,
      'cookie': {
        'did': device.did,
        'channelHex': device.channel.hex()
      },
      'capabilities': [
        Capabilities.ALEXA,
        Capabilities.simple("Alexa.PowerController", "powerState"),
        Capabilities.simple("Alexa.PercentageController", "percentage"),
      ]
    }

  def _handle_on_off(self, req, state):
    bearer_token = req['endpoint']['scope']['token']
    giz_token = self._giz_token_from_bearer(bearer_token)
    did = req['endpoint']['cookie']['did']
    channel_hex = req['endpoint']['cookie']['channelHex']
    cmd = MotoCmd.UP if state == 'OFF' else MotoCmd.DOWN
    frame = CommandFrame(
      header=Header(0, 144, 5),
      frame_type=FrameType.DEVICE_EXECUTE_REQ,
      data=[
        FrameData(DataKeys.DEVICE_CMD.value, cmd.value),
        FrameData(DataKeys.DEVICE_ADDR_CHANNEL.value, bytes.fromhex(channel_hex))
      ]
    )
    self._api.control(giz_token, did, frame)
    return self._make_response(
      bearer_token=bearer_token,
      namespace='Alexa.PowerController',
      name='powerState',
      value=state,
      correlation_token=req['header']['correlationToken'],
      endpoint_id=req['endpoint']['endpointId']
    )

  def _make_response(self, bearer_token, namespace, name, value, correlation_token, endpoint_id):
    ret = json.dumps({
      "context": {
        "properties": [
          {
            "namespace": namespace,
            "name": name,
            "value": value,
            "timeOfSample": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "uncertaintyInMilliseconds": 200
          },
          {
            "namespace": "Alexa.EndpointHealth",
            "name": "connectivity",
            "value": {
              "value": "OK"
            },
            "timeOfSample": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "uncertaintyInMilliseconds": 200
          }
        ]
      },
      "event": {
        "header": {
          "namespace": "Alexa",
          "name": "Response",
          "payloadVersion": "3",
          "messageId": str(uuid4()),
          "correlationToken": correlation_token
        },
        "endpoint": {
          "scope": {
            "type": "BearerToken",
            "token": bearer_token
          },
          "endpointId": endpoint_id
        },
        "payload": {}
      }
    })
    return ret

  def _handle_pct(self, req):
    bearer_token = req['endpoint']['scope']['token']
    giz_token = self._giz_token_from_bearer(bearer_token)
    did = req['endpoint']['cookie']['did']
    channel_hex = req['endpoint']['cookie']['channelHex']
    pct = req['payload']['percentage']
    frame = CommandFrame(
      header=Header(0, 144, 5),
      frame_type=FrameType.DEVICE_EXECUTE_REQ,
      data=[
        FrameData(DataKeys.DEVICE_CMD.value, MotoCmd.PERCENT_RUNING_LIGHT_DIMMER.value),
        FrameData(DataKeys.DEVICE_ADDR_CHANNEL.value, bytes.fromhex(channel_hex)),
        FrameData(DataKeys.DEVICE_CMD_DATA.value, bytes([1, pct, 0]))
      ]
    )
    self._api.control(giz_token, did, frame)
    return self._make_response(
      bearer_token=bearer_token,
      namespace='Alexa.PercentageController',
      name='percentage',
      value=pct,
      correlation_token=req['header']['correlationToken'],
      endpoint_id=req['endpoint']['endpointId']
    )