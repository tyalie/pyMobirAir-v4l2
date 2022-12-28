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
class MeasureParam:
  realtimeTshutter: float = 0
  realtimeTfpa: float = 0
  realtimeTlens: float = 0

  currChangeRTfpgIdx: int = 0

  lastShutterTshutter: float = 0
  lastShutterTfpa: float = 0
  lastShutterTlens: float = 0

  emission: int = 98
  humidity: int = 79
  distance: int = 10
  reflectT: float = 0

  ks: int = 0
  k0: int = 0
  k1: int = 0
  k2: int = 0
  k3: int = 0
  k4: int = 0
  k5: int = 0
  b: int = 0
  kf: int = 0
  kj: int = 10000

  tref: float = 0


  def setFromFrame(self, frame: RawFrame, module_tp: Optional[int]):
    self.realtimeTshutter = frame.fixedParam.realtimeShutterTemp
    self.realtimeTlens = frame.fixedParam.realtimeLensTemp
    if module_tp is not None:
      self.realtimeTfpa = frame.fixedParam.getRealtimeFpaTemp(module_tp)

    self.emission = frame.customParam.emission
    self.humidity = frame.customParam.humidity
    self.distance = frame.customParam.distance
    self.reflectT = frame.customParam.env_temp

    self.ks = frame.customParam.ks
    self.k0 = frame.customParam.k0
    self.k1 = frame.customParam.k1
    self.k2 = frame.customParam.k2
    self.k3 = frame.customParam.k3
    self.k4 = frame.customParam.k4
    self.k5 = frame.customParam.k5
    self.b  = frame.customParam.b
    self.kf = frame.customParam.kf
    self.tref = frame.customParam.tref / 100


@dataclass
class MobirAirState:
  width: int
  height: int
  refHeight: int
  jwbTabNumber: int = 0

  measureParam: MeasureParam = field(default_factory=MeasureParam)

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
  kjLastShutterTlens: float = 0
  lastAvgShutter: float = 0

  y16_k0: int = 0
  y16_k1: int = 0

  tFpaDelta: float = FPATemps.TFPA_DEFAULT

  def __post_init__(self):
    # initialize calibration / shutter frame
    self.shutterFrame = np.zeros((self.height - self.refHeight, self.width), dtype="<u2")

  def getCurrKArr(self) -> np.ndarray:
    if self.allKdata is None:
      raise Exception

    return self.allKdata[self.measureParam.currChangeRTfpgIdx][self.refHeight:,:]

  @property
  def currCurve(self) -> np.ndarray:
    if self.allCurveData is None:
      raise UninitializedValueAccess()

    n = max(1, self.measureParam.currChangeRTfpgIdx)
    return self.allCurveData[n - 1]

  @property
  def nearCurve(self) -> np.ndarray:
    if self.allCurveData is None:
      raise UninitializedValueAccess()

    n = max(1, self.measureParam.currChangeRTfpgIdx)
    return self.allCurveData[n]


