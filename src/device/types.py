from typing import Type
import dataclasses
from dataclasses import dataclass
import numpy as np

from device.temputils import MobirAirTempUtils

def bytefield(location: int, length: int = 2, order: str = "little", signed: bool = False):
  return dataclasses.field(
    metadata=dict(location=location, length=length, order=order, signed=signed)
  )

def bitfield(location: int, bits: int, length: int = 2):
  return dataclasses.field(
    metadata=dict(location=location, bits=bits, length=length)
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
class CustomParamLine:
  temp_range: int = bytefield(0x60)

  customParamInit: int = bytefield(0x63, length=1)
  humidity: int = bytefield(0x65, length=1)
  emission: int = bytefield(0x64, length=1)
  distance: int = bitfield(0x66, 0x003f)
  env_temp: int = bitfield(0x66, 0x7fc0)

  brightness: int = bytefield(0x69, length=1)
  contrast: int = bytefield(0x68, length=1)

  frequency_hz: int = bitfield(0x6a, 0xf0)

  autotiming_shutter: bool = bitfield(0x6c, 0b1)
  timing_shutter_time: int = bytefield(0x6e)

  ks: int = bytefield(0x90)
  k0: int = bytefield(0x92)
  k1: int = bytefield(0x94)
  k2: int = bytefield(0x96)
  k3: int = bytefield(0x98)
  k4: int = bytefield(0x9a)
  k5: int = bytefield(0x9c)
  b: int = bytefield(0x9e)
  kf: int = bytefield(0xa0)
  tref: int = bytefield(0xa2)

  @classmethod
  def new(cls, raw: bytes) -> 'CustomParamLine':
    return raw_to_dataclass(cls, raw)


@dataclass()
class RawFrame:
  header: bytes
  payload: bytes
  fixedParam: FixedParamLine
  customParam: CustomParamLine

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
      if "bits" not in meta:
        val = int.from_bytes(segment, byteorder=meta["order"], signed=meta["signed"])
      else:
        val = int.from_bytes(segment, byteorder="little", signed=False)
        val = (val & meta["bits"]) >> (bin(meta["bits"]).rindex("1") - 1)

      if field.type == bool:
        val = bool(val)

    elif field.type == str:
      val = segment.decode("ascii")

    values[field.name] = val

  return dataclass(**values)

