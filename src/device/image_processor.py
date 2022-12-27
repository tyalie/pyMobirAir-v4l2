from device.device_state import MobirAirState
from .types import Frame, RawFrame
from dataclasses import asdict
import numpy as np


class ThermalFrameProcessor:
  def __init__(self, state: MobirAirState) -> None:
    self._state = state


  def process(self, frame: RawFrame) -> Frame:
    image = np.frombuffer(frame.payload, dtype="<u2") \
      .reshape((self._state.height, self._state.width))

    if frame.fixedParam.isShuttering:
      self._handleShutter(image)
    else:
      image = self._normal_processing(image)

    return Frame(
      image=image,
      **frame.__dict__
    )

  def _handleShutter(self, img: np.ndarray):
    self._state.shutterFrame = img

  def _normal_processing(self, img: np.ndarray) -> np.ndarray:
    img = self.doBasicCalibration(img)

    return img

  def doBasicCalibration(self, img: np.ndarray) -> np.ndarray:
    avg = np.average(self._state.shutterFrame)
    img = img.astype("i4")

    return (avg + (img - self._state.shutterFrame)).astype("<u2")

