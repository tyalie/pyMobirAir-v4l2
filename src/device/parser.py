from typing import Optional
from device.device_state import MobirAirState

from device.types import CustomParamLine, FixedParamLine, RawFrame

class MobirAirParser:
  FRAME_START = bytes.fromhex("55aa2700")
  FRAME_HEADER_LENGTH = 240
  IMAGE_DEPTH = 2

  def __init__(self, state: MobirAirState) -> None:
    self._stream: bytearray = bytearray()
    self.width = state.width
    self.height = state.height

  def parse_stream(self, raw: bytes) -> Optional[RawFrame]:
    self._stream.extend(raw)
    i = self._stream.find(self.FRAME_START)

    if i >= 0 and (len(self._stream) - i) >= self.frame_size:
      if i > 0:
        print(f"parser: i started with offset {i}")

      frame_data = self._stream[i:i + self.frame_size]
      # resize stream data
      self._stream = self._stream[i + self.frame_size:]
      return self._parse_frame(frame_data)

    return None

  def _parse_frame(self, raw: bytes) -> RawFrame:
    header = raw[:self.FRAME_HEADER_LENGTH]
    fixedParam = FixedParamLine.new(header)

    if fixedParam.width != self.width or fixedParam.height != self.height:
      raise Exception(f"Frame parser came across frame with invalid size {fixedParam.width}x{fixedParam.height}")

    customParam = CustomParamLine.new(header)


    return RawFrame(
      header=header,
      payload=raw[self.FRAME_HEADER_LENGTH:],
      fixedParam=fixedParam,
      customParam=customParam
    )

  @property
  def frame_size(self):
    return self.width * self.height * self.IMAGE_DEPTH + self.FRAME_HEADER_LENGTH
