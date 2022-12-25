from typing import Callable
import usb.core
from .usb_wrapper import MobirAirUSBWrapper
from .types import Frame
from .parser import MobirAirParser
from .image_processor import ThermalFrameProcessor
import time

from threading import Thread


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
    self._recv_thread = Thread(target=self._read_data_listener)
    self._recv_thread.start()

  def set_frame_listener(self, listener: Callable[[Frame], None]):
    self._listener = listener

  def start_stream(self):
    self.stop_stream()
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

  def _read_data_listener(self):
    while True:
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

