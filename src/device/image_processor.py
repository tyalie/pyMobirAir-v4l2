from device.device_state import MobirAirState
from device.temputils import MobirAirTempUtils
from .types import Frame, RawFrame
import numpy as np
import logging


class ThermalFrameProcessor:
  def __init__(self, state: MobirAirState) -> None:
    self._state = state
    self._temp = MobirAirTempUtils(state)

  def process(self, frame: RawFrame) -> Frame:
    image = np.frombuffer(frame.payload, dtype="<u2") \
      .reshape((self._state.height, self._state.width))
    # remove reference rows, that are not used otherwise
    image = image[self._state.refHeight:,:]

    if frame.fixedParam.isShuttering:
      self._handleShutter(image)
    else:
      image = self._normal_processing(image)

    image = self._temperature_proc(image)

    return Frame(
      image=image,
      **frame.__dict__
    )

  def _temperature_proc(self, img: np.ndarray):
    img = self._temp.y16toTemp(img)
    return (img * 100).astype("i2")

  def _handleShutter(self, img: np.ndarray):
    self._state.shutterFrame = img

  def _normal_processing(self, img: np.ndarray) -> np.ndarray:
    if self._state.config.doNUC:
      img = self.doNUCbyTwoPoint(img)
    elif self._state.config.useCalib:
      img = self.doBasicCalibration(img)

    return img

  def doNUCbyTwoPoint(self, img: np.ndarray) -> np.ndarray:
    if self._state.allKdata is None:
      logging.error("allKdata is none")
      return img

    # `∀i: y16arr[i] = ⌊ avgSingleB + (frame[i] - bArr[i]) * kArr[i] / 2¹³ ⌋`
    avg = np.average(self._state.shutterFrame)
    img = img.astype("i4")

    return np.floor(
      avg + (img - self._state.shutterFrame) * self._state.getCurrKArr() / 2**13
    ).astype("u2")

  def doBasicCalibration(self, img: np.ndarray) -> np.ndarray:
    avg = np.average(self._state.shutterFrame)
    img = img.astype("i4")

    return (avg + (img - self._state.shutterFrame)).astype("<u2")


