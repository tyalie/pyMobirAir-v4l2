from typing import Optional
from enum import Enum
import numpy as np
from dataclasses import dataclass, field

from device.types import RawFrame

class UninitializedValueAccess(Exception):
  ...

class FPATemps(float, Enum):
  TFPA_DEFAULT = 0.15
  TFPA_DELTA = 0.18
  TFPA_DELTA_EXCEPTION = 0.3

@dataclass
class MobirAirConfig:
  doNUC: bool = True
  useCalib: bool = True


@dataclass
class MobirAirState:
  width: int
  height: int
  jwbTabNumber: int = 0

  currChangeRTfpgIdx: int = 0

  module_tp: Optional[int] = None

  allCurveData: Optional[np.ndarray] = None

  # calibration
  allKdata: Optional[np.ndarray] = None

  jwbTabArrShort: Optional[np.ndarray] = None

  # calibration - live
  shutterFrame: np.ndarray = field(init=False)

  # program config
  config: MobirAirConfig = field(default_factory=MobirAirConfig)

  # values
  lastShutterTfpa: float = 0
  lastShutterTlens: float = 0
  lastAvgShutter: float = 0

  y16_k0: int = 0
  y16_k1: int = 0

  kj: int = 10000

  tFpaDelta: float = FPATemps.TFPA_DEFAULT

  lastFrame: Optional[RawFrame] = None

  def __post_init__(self):
    # initialize calibration / shutter frame
    self.shutterFrame = np.zeros((self.height, self.width), dtype="<u2")

  def getCurrKArr(self) -> np.ndarray:
    if self.allKdata is None:
      raise Exception

    return self.allKdata[self.currChangeRTfpgIdx]

  @property
  def currCurve(self) -> np.ndarray:
    if self.allCurveData is None:
      raise UninitializedValueAccess()

    n = max(1, self.currChangeRTfpgIdx)
    return self.allCurveData[n - 1]

  @property
  def nearCurve(self) -> np.ndarray:
    if self.allCurveData is None:
      raise UninitializedValueAccess()

    n = max(1, self.currChangeRTfpgIdx)
    return self.allCurveData[n]


