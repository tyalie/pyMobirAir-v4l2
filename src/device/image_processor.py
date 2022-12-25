from .types import Frame, RawFrame
from dataclasses import asdict
import numpy as np


class ThermalFrameProcessor:
  def __init__(self, width: int, height: int) -> None:
    self.width = width
    self.height = height

    # initialize calibration frame
    self._calibration = np.zeros((self.width, self.height), dtype="<i4")

  def process(self, frame: RawFrame) -> Frame:
    image = np.frombuffer(frame.payload, dtype="<u2") \
      .reshape((self.width, self.height))

    if frame.fixedParam.isShuttering:
      cal_img = image.astype("i4") - np.average(image)
      self._calibration = (self._calibration * 70 + cal_img * 30) // 100
    else:
      image = (image - self._calibration).astype(image.dtype)

    return Frame(
      image=image,
      **frame.__dict__
    )
