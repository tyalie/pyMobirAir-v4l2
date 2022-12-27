from typing import Optional
from .usb_wrapper import MobirAirUSBWrapper

class USBReadFailedException(Exception):
  ...

class MobirAirUSBProtocol:
  MAX_GET_ARM_LENGTH = 51200

  def __init__(self, usb: MobirAirUSBWrapper) -> None:
    self._usb = usb
    pass

  def get_arm_param(self, address, length) -> bytes:
    def to_bytes(v: int) -> bytes:
      return v.to_bytes(2, "little", signed=False)

    buffer = bytearray()
    for s in range(address, address + length, self.MAX_GET_ARM_LENGTH):
      caddress = s // 0x800
      coffset = address % 0x100
      clength = min(address + length - s, self.MAX_GET_ARM_LENGTH)

      cmd_args = to_bytes(caddress) + to_bytes(coffset) + to_bytes(clength)
      cmd = b"GetArmParam=" + cmd_args

      data = self._usb.retrieve_data(cmd, clength)
      if data is None:
        raise USBReadFailedException
      buffer.extend(data)

    return buffer


  def setStream(self, state: bool):
    if state:
      self._usb.epo.write("StartX=1")
    else:
      self._usb.epo.write("StopX=1")

  def setShutter(self, state: bool):
    if state:
      self._usb.epo.write("ShutterOff=1")
    else:
      self._usb.epo.write("ShutterOn=1")

  def doNUC(self):
    self._usb.epo.write("DoNUC=1")
