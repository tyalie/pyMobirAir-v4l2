from typing import Callable
import usb.core
import numpy as np

from device.device_state import FPATemps, MobirAirState
from device.shutterhandling import ShutterHandler
from device.temputils import MobirAirTempUtils
from .usb_wrapper import MobirAirUSBWrapper
from .types import Frame, RawFrame
from .parser import MobirAirParser
from .image_processor import ThermalFrameProcessor
from .protocol import MobirAirUSBProtocol
import time

from threading import Thread, Event


class MobirAirDriver:
  WIDTH = 120
  HEIGHT = 92

  def __init__(self) -> None:
    self._listener = None

    self._state = MobirAirState(self.WIDTH, self.HEIGHT)

    dev = MobirAirUSBWrapper.find_device()
    self._usb = MobirAirUSBWrapper(dev)
    self._protocol = MobirAirUSBProtocol(self._usb)

    self._parser = MobirAirParser(self._state)
    self._img_proc = ThermalFrameProcessor(self._state)
    self._shutter = ShutterHandler(self._protocol, self._state)
    self._shutter.setShutterFinishCallback(self._afterShutterCallback)

    self._temp = MobirAirTempUtils(self._state)

    # register incoming data listener
    self._enable_recv_thread = Event()
    self._recv_thread = Thread(
      target=self._read_data_listener, args=(self._enable_recv_thread,))
    self._recv_thread.start()

    # init state
    self._init_state()


  def stop(self):
    """ Method to stop the MobirAir USB device.
    This turned out to be a bit more complicated than expected.
    During application start the device will be resetted. This
    seems to be troublesome, when the stream is still enabled,
    as the device will not return anything until a power cycle.

    This method seems to do the job thoo.
    """
    self.clear_device()
    time.sleep(0.1)
    del self._usb

  def clear_device(self):
    self._protocol.setShutter(True)
    self._protocol.setStream(False)
    time.sleep(0.1)
    self._protocol.setStream(False)
    time.sleep(0.1)

    while True:
      try:
        self._usb.epi.read(self._usb.epi.wMaxPacketSize, 100)
      except usb.core.USBTimeoutError:
        return

  def set_frame_listener(self, listener: Callable[[Frame], None]):
    self._listener = listener

  def start_stream(self):
    self._enable_recv_thread.set()
    self._protocol.setStream(True)
    self._shutter.doShutter()

  def stop_stream(self):
    self._protocol.setStream(False)
    self._enable_recv_thread.clear()


  ###### stream functions ######
  def _read_data_listener(self, should_process: Event):
    frames = 0

    while True:
      should_process.wait()

      try:
        data = self._usb.epi.read(8192, timeout=200)
        _t_start = time.monotonic_ns()
        data = data.tobytes()

        raw_frame = self._parser.parse_stream(data)

        if raw_frame is not None:
          frame = self._img_proc.process(raw_frame)

          _t_end = time.monotonic_ns()
          if _t_end - _t_start > 2e6:
            print(f"Δt = {(_t_end - _t_start) / 1e6:.2f}ms")

          if self._listener is not None:
            self._listener(frame)

          self._state.measureParam.setFromFrame(raw_frame, self._state.module_tp)
          if frames % 25 == 0:
            self._changeR()
            frames = 0
          frames += 1

          self._shutter.automaticShutter()

      except usb.core.USBTimeoutError:
        print("timeout")
      except usb.core.USBError as e:
        print("Stopping receive")
        raise e

  def _changeR(self):
    """Method to change detect index
    Seems to depend on the fpa temperature, using the
    jwb short array.

    The detect index is relevant for the camera and the
    raw value processing (e.g. selects k data frame)
    """
    if self._state.module_tp is None:
      return

    realtimeTfpa = self._state.measureParam.realtimeTfpa * 100

    if self._state.jwbTabArrShort is None:
      print("warn: jwbTabArrShort not initialized")
      return

    changeRidx = 1
    if realtimeTfpa <= self._state.jwbTabArrShort[0]:
      changeRidx = 0
    elif realtimeTfpa >= self._state.jwbTabArrShort[-1]:
      changeRidx = self._state.jwbTabNumber - 1
    else:
      while True:
        if realtimeTfpa < self._state.jwbTabArrShort[changeRidx]:
          if self._state.measureParam.currChangeRTfpgIdx == (changeRidx - 1):
            if not (realtimeTfpa - self._state.jwbTabArrShort[changeRidx - 1] < 50):
              break

            changeRidx -= 1
            break

          if self._state.measureParam.currChangeRTfpgIdx != (changeRidx - 1):
            break

          if not (self._state.jwbTabArrShort[changeRidx] - realtimeTfpa < 50):
            break

          changeRidx += 1
          break

        changeRidx += 1

    if self._state.measureParam.currChangeRTfpgIdx != changeRidx:
      print(f"Setting new changeRidx: {changeRidx}")
      self._state.measureParam.currChangeRTfpgIdx = changeRidx
      self._protocol.setChangeR(changeRidx)
      self._shutter.manualShutter()


  #### shuttering ####
  def _afterShutterCallback(self, usingNUC: bool):
    self.calcMeasureKj(usingNUC)

  def calcMeasureKj(self, usingNUC: bool):
    deltaTlens = (self._state.measureParam.realtimeTlens - self._state.kjLastShutterTlens)
    print(f"Δlens = {deltaTlens}")

    self._state.y16_k0 = self._state.y16_k1
    self._state.y16_k1 = self._temp.getY16byShutterTemp(self._state.measureParam.realtimeTshutter)

    if usingNUC:
      if abs(deltaTlens) > self._state.tFpaDelta:
        if self._state.y16_k0 == 0:
          self._state.y16_k1 = self._state.y16_k0

        lastLastAvgShutter = self._state.lastAvgShutter
        self._state.lastAvgShutter = float(np.average(self._state.shutterFrame))

        if lastLastAvgShutter == 0:
          lastLastAvgShutter = self._state.lastAvgShutter

        deltaS = self._state.lastAvgShutter - lastLastAvgShutter

        f = (deltaS - (self._state.y16_k1 - self._state.y16_k0)) / deltaTlens

        if 10 < abs(f) < 100:
          self._state.measureParam.kj = int(f * 100)
          print(f"setting new kj: {self._state.measureParam.kj}")

        self._state.tFpaDelta = FPATemps.TFPA_DELTA
        self._state.kjLastShutterTlens = self._state.measureParam.realtimeTlens
      else:
        self._state.tFpaDelta = FPATemps.TFPA_DELTA_EXCEPTION
    else:
      self._state.lastAvgShutter = float(np.average(self._state.shutterFrame))
      self._state.kjLastShutterTlens = self._state.measureParam.realtimeTlens


  ###### DATA ######
  def _init_state(self):
    # module tp
    self._state.module_tp = self._protocol.getModuleTP()

    # get jwb tab number
    self._state.jwbTabNumber = self._protocol.getJwbTabNum()

    # get jwb short array
    tabarr = self._protocol.getJwbTabArrShort(self._state.jwbTabNumber)
    self._state.jwbTabArrShort = np.frombuffer(tabarr, dtype="<u2")

    # get k data
    kdata_raw = self._protocol.getAllKData(self.WIDTH, self.HEIGHT, self._state.jwbTabNumber)
    kdata = np.frombuffer(kdata_raw, dtype="<u2") \
      .reshape((self._state.jwbTabNumber, self._state.height, self._state.width))
    self._state.allKdata = kdata

    # get all curve data
    curve_raw = self._protocol.getAllCurveData(self._state.jwbTabNumber)
    curve = np.frombuffer(curve_raw, dtype="<u2") \
      .reshape((self._state.jwbTabNumber, 1700))
    self._state.allCurveData = curve

    print(f"state: {self._state}")
