from typing import Optional
import numpy as np
from dataclasses import dataclass, field

@dataclass
class MobirAirConfig:
  doNUC: bool = True
  useCalib: bool = True


@dataclass
class MobirAirState:
  width: int
  height: int
  jwbTabNumber: int = 0

  currChangeRidx: int = 0

  module_tp: Optional[int] = None

  # calibration
  allKdata: Optional[np.ndarray] = None

  jwbTabArrShort: Optional[np.ndarray] = None

  # calibration - live
  shutterFrame: np.ndarray = field(init=False)

  # program config
  config: MobirAirConfig = field(default_factory=MobirAirConfig)

  def __post_init__(self):
    # initialize calibration / shutter frame
    self.shutterFrame = np.zeros((self.height, self.width), dtype="<u2")

  def getCurrKArr(self) -> np.ndarray:
    if self.allKdata is None:
      raise Exception

    return self.allKdata[self.currChangeRidx]


