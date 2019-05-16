from dataclasses import dataclass
from enum import Enum


class DataKeyType(Enum):
  STRING = 1
  BYTE = 2
  BYTES = 3
  UINT8 = 4
  UINT16 = 5
  UINT32 = 6


@dataclass
class DataKey:
  key_id: int
  name: str
  key_type: DataKeyType


class DataKeys(Enum):
  HOST_VERSION = DataKey(1, "HOST_VERSION", DataKeyType.STRING)
  CLIENT_TYPE = DataKey(2, "CLIENT_TYPE", DataKeyType.BYTE)
  AUTH_RESULT = DataKey(5, "AUTH_RESULT", DataKeyType.BYTE)
  ERROR_CODE = DataKey(6, "ERROR_CODE", DataKeyType.BYTE)
  HOST_TYPE = DataKey(7, "HOST_TYPE", DataKeyType.BYTE)
  HOST_NAME = DataKey(8, "HOST_NAME", DataKeyType.STRING)
  HOST_IP = DataKey(9, "HOST_IP", DataKeyType.STRING)
  HOST_PORT = DataKey(10, "HOST_PORT", DataKeyType.UINT16)
  TIME = DataKey(12, "TIME", DataKeyType.BYTES)
  DELAY_TIME = DataKey(13, "DELAY_TIME", DataKeyType.UINT16)
  NAME = DataKey(14, "NAME", DataKeyType.STRING)
  PICTURE = DataKey(15, "PICTURE", DataKeyType.BYTE)
  NUMBER = DataKey(16, "NUMBER", DataKeyType.UINT8)
  SERIAL_NO = DataKey(17, "SERIAL_NO", DataKeyType.BYTE)
  USER_NAME = DataKey(18, "USER_NAME", DataKeyType.STRING)
  USER_PASSWD = DataKey(19, "USER_PASSWD", DataKeyType.STRING)
  USER_ROLE = DataKey(20, "USER_ROLE", DataKeyType.BYTE)
  HOST_MAC = DataKey(23, "HOST_MAC", DataKeyType.BYTES)
  DEVICE_ADDR_CHANNEL = DataKey(257, "DEVICE_ADDR_CHANNEL", DataKeyType.BYTES)
  DEVICE_TYPE = DataKey(258, "DEVICE_TYPE", DataKeyType.UINT16)
  DEVICE_CMD = DataKey(259, "DEVICE_CMD", DataKeyType.BYTE)
  DEVICE_CMD_DATA = DataKey(260, "DEVICE_CMD_DATA", DataKeyType.BYTES)
  DEVICE_KIND = DataKey(261, "DEVICE_KIND", DataKeyType.BYTE)
  DEVICE_SECRET_KEY = DataKey(262, "DEVICE_SECRET_KEY", DataKeyType.BYTE)
  DEVICE_CHANNEL = DataKey(265, "DEVICE_CHANNEL", DataKeyType.UINT8)
  DEVICE_ATTR = DataKey(268, "DEVICE_ATTR", DataKeyType.BYTE)
  EMITTER_KEY_NUMBER = DataKey(272, "EMITTER_KEY_NUMBER", DataKeyType.UINT8)
  TRANSVERTER_CHANNEL_NUMBER = DataKey(273, "TRANSVERTER_CHANNEL_NUMBER",
                                       DataKeyType.UINT8)
  ROOM_ID = DataKey(512, "ROOM_ID", DataKeyType.BYTES)
  SCENE_ID = DataKey(528, "SCENE_ID", DataKeyType.BYTES)
  SCENE_EXECUTE_MODE = DataKey(529, "SCENE_EXECUTE_MODE", DataKeyType.UINT8)
  SCENE_ADD_MODE = DataKey(530, "SCENE_ADD_MODE", DataKeyType.UINT8)
  SCENE_CMD_NUMBER = DataKey(531, "SCENE_CMD_NUMBER", DataKeyType.UINT8)
  TIMER_ID = DataKey(544, "TIMER_ID", DataKeyType.BYTES)
  TIMER_ONOFF_MARK = DataKey(545, "TIMER_ONOFF_MARK", DataKeyType.UINT8)
  TIMER_LOOP_MARK = DataKey(546, "TIMER_LOOP_MARK", DataKeyType.UINT32)
  START_TIME = DataKey(568, "START_TIME", DataKeyType.BYTES)
  END_TIME = DataKey(569, "END_TIME", DataKeyType.BYTES)
  LIST_ID = DataKey(570, "LIST_ID", DataKeyType.BYTE)
  HOUR = DataKey(571, "HOUR", DataKeyType.BYTE)
  MINUTE = DataKey(572, "MINUTE", DataKeyType.BYTE)
  TIMER_CMD_TYPE = DataKey(573, "TIMER_CMD_TYPE", DataKeyType.UINT8)
  INNER_PARA_BYTES_COUNT = DataKey(577, "INNER_PARA_BYTES_COUNT",
                                   DataKeyType.BYTE)
  PARA_START_ADDR = DataKey(578, "PARA_START_ADDR", DataKeyType.UINT8)
  INNER_PARA_DATA = DataKey(579, "INNER_PARA_DATA", DataKeyType.BYTES)
  USER_AUTHORITY = DataKey(592, "USER_AUTHORITY", DataKeyType.UINT8)
  SCENE_ATTR = DataKey(593, "SCENE_ATTR", DataKeyType.UINT8)
  HUB_CHECK_CODE = DataKey(594, "HUB_CHECK_CODE", DataKeyType.UINT16)
  MCU_SOFTWARE_VERSION = DataKey(595, "MCU_SOFTWARE_VERSION",
                                 DataKeyType.STRING)
  WIFI_SOFTWARE_VERSION = DataKey(596, "WIFI_SOFTWARE_VERSION",
                                  DataKeyType.STRING)
  WIFI_HARDWARE_VERSION = DataKey(597, "WIFI_HARDWARE_VERSION",
                                  DataKeyType.STRING)
  WIFI_MAC_ADDR = DataKey(598, "WIFI_MAC_ADDR", DataKeyType.BYTES)
  WIFI_IP = DataKey(599, "WIFI_IP", DataKeyType.STRING)
  WIFI_SECRET_KEY = DataKey(608, "WIFI_SECRET_KEY", DataKeyType.UINT8)
  TDBU_PART = DataKey(630, "TDBU_PART", DataKeyType.BYTE)
  TDBU_ID = DataKey(631, "TDBU_ID", DataKeyType.BYTES)
  RS485_MAC = DataKey(632, "RS485_MAC", DataKeyType.BYTES)
  ERROR = DataKey(768, "ERROR", DataKeyType.UINT16)


DATAKEYS_BY_ID = {
    dk.value.key_id: dk.value for (_, dk) in DataKeys.__members__.items()
}
