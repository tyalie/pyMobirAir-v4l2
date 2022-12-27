from typing import Optional
import numpy as np
from dataclasses import dataclass, field

from device.types import RawFrame

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
  lastShutterTfpa: int = 0
  lastShutterTlens: int = 0

  lastFrame: Optional[RawFrame] = None

  def __post_init__(self):
    # initialize calibration / shutter frame
    self.shutterFrame = np.zeros((self.height, self.width), dtype="<u2")

  def getCurrKArr(self) -> np.ndarray:
    if self.allKdata is None:
      raise Exception

    return self.allKdata[self.currChangeRTfpgIdx]

  @property
  def currCurve(self) -> Optional[np.ndarray]:
    if self.allCurveData is None:
      return None

    n = max(1, self.currChangeRTfpgIdx)
    return self.allCurveData[n - 1]

  @property
  def nearCurve(self) -> Optional[np.ndarray]:
    if self.allCurveData is None:
      return None

    n = max(1, self.currChangeRTfpgIdx)
    return self.allCurveData[n]


