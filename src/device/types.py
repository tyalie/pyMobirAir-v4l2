from typing import Tuple, Type
import dataclasses
from dataclasses import dataclass
import numpy as np

def bytefield(location: int, length: int, order: str = "little", signed: bool = False):
  return dataclasses.field(
    metadata=dict(location=location, length=length, order=order, signed=signed)
  )

@dataclass()
class FixedParamLine:
  width: int = bytefield(0x4,2)
  height: int = bytefield(0x6,2)
  device_name: str = bytefield(0x8, 8)
  isShuttering: bool = bytefield(0x18, 2)

  @classmethod
  def new(cls, raw: bytes) -> 'FixedParamLine':
    return raw_to_dataclass(cls, raw)

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

