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

  def setChangeR(self, Ridx: int):
    cmd = b"SetDetectIndex=" + Ridx.to_bytes(byteorder="little", length=2)
    self._usb.epo.write(cmd)

  ##### data from device #####
  def getAllKData(self, width: int, height: int, number: int) -> bytes:
    img_size = 2 * width * height * number
    return self.get_arm_param(300 * 0x800, img_size)

  def getAllCurveData(self, number: int) -> bytes:
    size = number * 1700 * 2
    return self.get_arm_param(462 * 0x800, size)

  def getJwbTabNum(self) -> int:
    return int.from_bytes(self.get_arm_param(488 * 0x800, 2), byteorder="little")

  def getJwbTabArrShort(self, number: int) -> bytes:
    return self.get_arm_param(487 * 0x800, number * 2)

  def getDeviceSN(self) -> bytes:
    return self.get_arm_param(489 * 0x800, 14)

  def getModuleTP(self) -> int:
    return self.get_arm_param(490 * 0x800, 1)[0]
