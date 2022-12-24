from typing import Optional
import numpy as np

from device.types import Frame

class MobirAirParser:
  FRAME_START = bytes.fromhex("55aa2700")
  FRAME_HEADER_LENGTH = 240
  IMAGE_DEPTH = 2

  def __init__(self, width: int, height: int) -> None:
    self._stream: bytearray = bytearray()
    self.width = width
    self.height = height

  def parse_stream(self, raw: bytes) -> Optional[Frame]:
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

  def _parse_frame(self, raw: bytes) -> Frame:
    width = int.from_bytes(raw[4:6], byteorder="little", signed=False)
    height = int.from_bytes(raw[6:8], byteorder="little", signed=False)

    if width != self.width or height != self.height:
      raise Exception(f"Frame parser came across frame with invalid size {width}x{height}")

    payload = raw[self.FRAME_HEADER_LENGTH:]
    image = np.frombuffer(payload, dtype="<u2")

    return Frame(
      header=raw[:self.FRAME_HEADER_LENGTH],
      payload=payload,
      image=image.reshape((width, height))
    )

  @property
  def frame_size(self):
    return self.width * self.height * self.IMAGE_DEPTH + self.FRAME_HEADER_LENGTH
