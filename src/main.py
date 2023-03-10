#!/usr/bin/env python3
from device import MobirAirDriver, Frame
from video.loopback import create_loopback
import signal
import sys
import numpy as np
import logging
import argparse

logging.basicConfig(level=logging.DEBUG)

def abs_diff(img1, img2):
  a = img1 - img2
  b = np.uint16(img1 < img2) * (2**16 - 2) + 1
  return a * b


driver = None

def sigint_handler(sig, frame):
  logging.info("Handled sigint")
  try:
    if driver is not None:
      driver.stop()
  finally:
    sys.exit(0)


def main(video_device: str):
  global driver
  signal.signal(signal.SIGINT, sigint_handler)

  stream = create_loopback(video_device, MobirAirDriver.WIDTH, MobirAirDriver.HEIGHT - MobirAirDriver.REF_HEIGHT)
  frame_count = 0
  def listener(f: Frame):
    nonlocal frame_count

    if frame_count % 25 == 0:
      logging.debug(f"Δtemps = {np.min(f.image) / 100 - 273.15:.2f} - {np.max(f.image) / 100 - 273.15:.2f} °C")
    frame_count += 1

    stream.write(f.image.tobytes(order='C'))

  driver = MobirAirDriver()
  driver.set_frame_listener(listener)
  driver.stop_stream()
  logging.info(f"Device: {driver._protocol.getDeviceSN().decode('UTF-8')}")

  driver.start_stream()


if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument(
    "-l", "--loopback",
    help="Path to the loopback device (e.g. /dev/videoX)", required=True
  )

  args = parser.parse_args()

  main(args.loopback)
