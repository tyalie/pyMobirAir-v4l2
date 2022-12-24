from dataclasses import dataclass
import numpy as np

@dataclass()
class Frame:
  header: bytes
  payload: bytes
  image: np.ndarray

  @property
  def raw(self) -> bytes:
    return self.header + self.payload
