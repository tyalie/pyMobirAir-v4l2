import time
from typing import Callable, Optional
from device.device_state import MobirAirState
from device.protocol import MobirAirUSBProtocol
from threading import Thread, Lock


class ShutterHandler:
  def __init__(self, protocol: MobirAirUSBProtocol, state: MobirAirState) -> None:
    self._protocol = protocol
    self._state: MobirAirState = state

    self.useNUC = True
    self._previous_shutter = 0
    self._thread_lock = Lock()

    self._shutter_finish_callback: Optional[Callable[[bool],None]] = None

  def setShutterFinishCallback(self, callback: Callable[[bool], None]):
    self._shutter_finish_callback = callback

  def doShutter(self):
    with self._thread_lock:
      self._previous_shutter = time.time()
      self._protocol.setShutter(True)
      time.sleep(0.4)

      self._state.measureParam.lastShutterTfpa = self._state.measureParam.realtimeTfpa
      self._state.measureParam.lastShutterTlens = self._state.measureParam.realtimeTlens

      if (self.useNUC):
        self._protocol.doNUC()
        time.sleep(2)

      self._protocol.setShutter(False)
      if self._shutter_finish_callback is not None:
        self._shutter_finish_callback(self.useNUC)

  @property
  def canDoShutter(self):
    return (time.time() - self._previous_shutter) > 5

  def manualShutter(self):
    if self.canDoShutter:
      Thread(target=self.doShutter).start()


  def automaticShutter(self):
    if (time.time() - self._previous_shutter) > 30:
      Thread(target=self.doShutter).start()
