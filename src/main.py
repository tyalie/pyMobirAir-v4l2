#!/usr/bin/env python3
from device import MobirAirDriver, Frame
from video.loopback import create_loopback
import signal
import sys
import time
import numpy as np
from matplotlib import pyplot as plt

def abs_diff(img1, img2):
  a = img1 - img2
  b = np.uint16(img1 < img2) * (2**16 - 2) + 1
  return a * b


driver = None

def sigint_handler(sig, frame):
  print("Handled sigint")
  try:
    if driver is not None:
      driver.stop()
  finally:
    sys.exit(0)


def main():
  global driver
  signal.signal(signal.SIGINT, sigint_handler)

  stream = create_loopback("/dev/video2", MobirAirDriver.WIDTH, MobirAirDriver.HEIGHT - MobirAirDriver.REF_HEIGHT)
  frame_count = 0
  def listener(f: Frame):
    nonlocal frame_count

    if frame_count % 25 == 0:
      print(f"Δtemps = {np.min(f.image) / 100} - {np.max(f.image) / 100} °C")
    frame_count += 1

    stream.write(f.image.tobytes(order='C'))

  driver = MobirAirDriver()
  driver.set_frame_listener(listener)
  driver.stop_stream()
  print("Device:", driver._protocol.getDeviceSN().decode("UTF-8"))

  driver.start_stream()


if __name__ == "__main__":
  main()
