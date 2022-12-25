from typing import Callable
import usb.core
from .usb_wrapper import MobirAirUSBWrapper
from .types import Frame
from .parser import MobirAirParser
from .image_processor import ThermalFrameProcessor
import time

from threading import Thread, Event


class MobirAirDriver:
  WIDTH = 120
  HEIGHT = 92

  def __init__(self) -> None:
    self._listener = None

    dev = MobirAirUSBWrapper.find_device()
    self._usb = MobirAirUSBWrapper(dev)
    self._parser = MobirAirParser(self.WIDTH, self.HEIGHT)
    self._img_proc = ThermalFrameProcessor(self.WIDTH, self.HEIGHT)

    # register incoming data listener
    self._enable_recv_thread = Event()
    self._recv_thread = Thread(
      target=self._read_data_listener, args=(self._enable_recv_thread,))
    self._recv_thread.start()

    # clear usb queue
    self.clear_device()

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
    self._usb.epo.write("StartX=1")
    time.sleep(1)
    #self._usb.epo.write("SetDetectIndex=\x02\x00")
    #time.sleep(1)
    self._usb.epo.write("ShutterOff=1")
    time.sleep(1)
    self._usb.epo.write("DoNUC=1")
    time.sleep(2)
    self._usb.epo.write("ShutterOn=1")
    time.sleep(1)

  def stop_stream(self):
    self._usb.epo.write("StopX=1\r")
    self._enable_recv_thread.clear()

  def _read_data_listener(self, should_process: Event):
    while True:
      should_process.wait()

      try:
        data = self._usb.epi.read(128, timeout=200)
        data = data.tobytes()

        raw_frame = self._parser.parse_stream(data)

        if raw_frame is not None:
          frame = self._img_proc.process(raw_frame)

          if self._listener is not None:
            self._listener(frame)
      except usb.core.USBTimeoutError:
        print("timeout")
        ...
      except usb.core.USBError as e:
        print("Stopping receive")
        raise e

