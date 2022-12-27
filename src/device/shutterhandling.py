import time
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

  def doShutter(self):
    with self._thread_lock:
      self._previous_shutter = time.time()
      self._protocol.setShutter(True)
      time.sleep(0.4)

      if (frame := self._state.lastFrame) is not None:
        self._state.lastShutterTfpa = frame.fixedParam.realtimeShutterTemp
        self._state.lastShutterTlens = frame.fixedParam.realtimeLensTemp

      if (self.useNUC):
        self._protocol.doNUC()
        time.sleep(2)

      self._protocol.setShutter(False)

  @property
  def canDoShutter(self):
    return (time.time() - self._previous_shutter) > 5

  def manualShutter(self):
    if self.canDoShutter:
      Thread(target=self.doShutter).start()


