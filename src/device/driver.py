from typing import Callable
import usb.core
import numpy as np

from device.device_state import MobirAirState
from .usb_wrapper import MobirAirUSBWrapper
from .types import Frame
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
    time.sleep(1)
    self._protocol.setShutter(True)
    time.sleep(1)
    self._protocol.doNUC()
    time.sleep(2)
    self._protocol.setShutter(False)
    time.sleep(1)

  def stop_stream(self):
    self._protocol.setStream(False)
    self._enable_recv_thread.clear()


  ###### stream functions ######
  def _read_data_listener(self, should_process: Event):
    while True:
      should_process.wait()

      try:
        data = self._usb.epi.read(128, timeout=200)
        _t_start = time.monotonic_ns()
        data = data.tobytes()

        raw_frame = self._parser.parse_stream(data)

        if raw_frame is not None:
          frame = self._img_proc.process(raw_frame)

          _t_end = time.monotonic_ns()
          print(f"Δt = {(_t_end - _t_start) / 1e6:.2f}ms")

          if self._listener is not None:
            self._listener(frame)
      except usb.core.USBTimeoutError:
        print("timeout")
      except usb.core.USBError as e:
        print("Stopping receive")
        raise e


  ###### DATA ######
  def _init_state(self):
    # get k data
    kdata_raw = self._protocol.getAllKData(self.WIDTH, self.HEIGHT, self._state.jwbTabNumber)
    kdata = np.frombuffer(kdata_raw, dtype="<u2") \
      .reshape((self._state.jwbTabNumber, self._state.height, self._state.width))
    self._state.allKdata = kdata



