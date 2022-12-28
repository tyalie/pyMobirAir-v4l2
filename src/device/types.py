from typing import Tuple, Type
import dataclasses
from dataclasses import dataclass
import numpy as np

from device.temputils import MobirAirTempUtils

def bytefield(location: int, length: int = 2, order: str = "little", signed: bool = False):
  return dataclasses.field(
    metadata=dict(location=location, length=length, order=order, signed=signed)
  )

@dataclass()
class FixedParamLine:
  width: int = bytefield(0x4)
  height: int = bytefield(0x6)
  device_name: str = bytefield(0x8, 8)

  _startupShutterTemp: int = bytefield(0x10)
  _realtimeShutterTemp: int = bytefield(0x12)
  _realtimeLensTemp: int = bytefield(0x14)
  _realtimeFpaTemp: int = bytefield(0x16)

  isShuttering: bool = bytefield(0x18)


  @classmethod
  def new(cls, raw: bytes) -> 'FixedParamLine':
    return raw_to_dataclass(cls, raw)

  def getRealtimeFpaTemp(self, module_tp: int) -> float:
    return MobirAirTempUtils.getFpaTemp(self._realtimeFpaTemp, module_tp)

  @property
  def realtimeLensTemp(self) -> float:
    return MobirAirTempUtils.getParamTemp(self._realtimeLensTemp)

  @property
  def realtimeShutterTemp(self) -> float:
    return MobirAirTempUtils.getParamTemp(self._realtimeShutterTemp)

  @property
  def startupShutterTemp(self) -> float:
    return MobirAirTempUtils.getParamTemp(self._startupShutterTemp)


@dataclass()
class RawFrame:
  header: bytes
  payload: bytes
  fixedParam: FixedParamLine

  @property
  def raw(self) -> bytes:
    return self.header + self.payload


@dataclass()
class Frame(RawFrame):
  image: np.ndarray


def raw_to_dataclass(dataclass: Type, raw: bytes):
  values = {}

  for field in dataclasses.fields(dataclass):
    meta = field.metadata
    segment = raw[meta["location"]:meta["location"] + meta["length"]]
    val = None

    if field.type == int or field.type == bool:
      val = int.from_bytes(segment, byteorder=meta["order"], signed=meta["signed"])
      if field.type == bool:
        val = bool(val)

    elif field.type == str:
      val = segment.decode("ascii")

    values[field.name] = val

  return dataclass(**values)

