import usb.core
import usb.util


class MobirAirUSBWrapper:
  def __init__(self, dev: usb.core.Device) -> None:
    self._dev = dev
    self._init()

  def _init(self):
    # reset device state
    self._dev.reset()

    # set active configuration, as there's only one use that
    self._dev.set_configuration()

    # get and store endpoint instance
    cfg: usb.core.Configuration = self._dev.get_active_configuration()
    self._interface = cfg[(1,1)]

    # TODO: why is this the solution
    # see here: https://stackoverflow.com/a/44123105
    self._interface.set_altsetting()

    # find endpoints
    def custom_match(type):
      def f(e):
        return usb.util.endpoint_direction(e.bEndpointAddress) == type
      return f

    self._endpoint_out: usb.core.Endpoint = usb.util.find_descriptor(
      self._interface, custom_match=custom_match(usb.util.ENDPOINT_OUT))
    self._endpoint_in: usb.core.Endpoint = usb.util.find_descriptor(
      self._interface, custom_match=custom_match(usb.util.ENDPOINT_IN))

    if self._endpoint_in is None or self._endpoint_out is None:
      raise Exception("endpoints couldn't be initialized")


  @property
  def epo(self) -> usb.core.Endpoint:
    return self._endpoint_out

  @property
  def epi(self) -> usb.core.Endpoint:
    return self._endpoint_in

  def __del__(self):
    print("disposing")
    usb.util.dispose_resources(self._dev)


  def retrieve_data(self, command: bytes, length: int, timeouts: int = 3):
    """Retrieve data with specified length from usb device using
    a command.

    Using the .read command can timeout, so one can specify the amount of
    max. allowed timeouts. Will return None if the limit has been archieved.

    This method is blocking, until all data has been received or
    timeouts have all been used up.
    """
    #
    self.epo.write(command)
    buffer = bytearray()
    while len(buffer) < length:
      try:
        #data = usb.core.array.array('B')
        data = self.epi.read(self.epi.wMaxPacketSize, timeout=200)
        buffer.extend(data.tobytes())

      except usb.core.USBTimeoutError:
        timeouts -= 1

      if timeouts == 0:
        print(f"Warn: run into timeout limit. Received {len(buffer)} bytes")
        return None

    if len(buffer) > length:
      print(f"Warn: expected buffer with length {length}, but got {len(buffer)}")
    return buffer[:length]


  @staticmethod
  def find_device() -> usb.core.Device:
    dev = usb.core.find(idVendor=0x0525)
    if dev == None:
      raise Exception("device not found")
    return dev
