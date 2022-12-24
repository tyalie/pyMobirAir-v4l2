#!/usr/bin/env python3
from device import MobirAirDriver, Frame
from video.loopback import create_loopback
import time
import numpy as np

def abs_diff(img1, img2):
  a = img1 - img2
  b = np.uint16(img1 < img2) * (2**16 - 2) + 1
  return a * b


def main():
  stream = create_loopback("/dev/video2", MobirAirDriver.WIDTH, MobirAirDriver.HEIGHT)

  previous_img = None
  def listener(f: Frame):
    nonlocal previous_img
    print(np.min(f.image), "/", np.max(f.image))

    if previous_img is not None:
      img = (np.uint32(f.image) - 4000) * 2**16 / (5000 - 4000)
      img = np.uint16(img)
      stream.write(img.tobytes(order='C'))

    previous_img = f.image

  driver = MobirAirDriver()
  driver.set_frame_listener(listener)
  driver.stop_stream()
  time.sleep(0.2)
  driver.start_stream()




if __name__ == "__main__":
  main()
