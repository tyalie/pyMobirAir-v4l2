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
  if driver is not None:
    driver.stop()
  sys.exit(0)


def main():
  global driver
  signal.signal(signal.SIGINT, sigint_handler)

  stream = create_loopback("/dev/video2", MobirAirDriver.WIDTH, MobirAirDriver.HEIGHT)

  previous_img = None
  def listener(f: Frame):
    nonlocal previous_img
    min = np.min(f.image[2:,:])
    max = np.max(f.image[2:,:])

    print(np.min(f.image), "/", np.max(f.image), f" / {min}-{max}")


    img = (np.uint32(f.image) - min) * (2**16 - 1) / (max - min)
    img = np.uint16(img)
    stream.write(img.tobytes(order='C'))

  driver = MobirAirDriver()
  driver.set_frame_listener(listener)
  driver.stop_stream()
  #time.sleep(0.2)

  img_size = 120 * 92 * 2
  data = driver.getAllKData(4)
  if data is not None:
    for n in range(4):
      img = np.frombuffer(data[n*img_size: (n+1) * img_size], dtype="<u2").reshape((92, 120))
      plt.imshow(img)
      plt.show()

  driver.start_stream()

  import termios, fcntl, sys, os
  fd = sys.stdin.fileno()

  oldterm = termios.tcgetattr(fd)
  newattr = termios.tcgetattr(fd)
  newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
  termios.tcsetattr(fd, termios.TCSANOW, newattr)

  oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
  fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

  try:
    conf = driver._state.config
    while 1:
      try:
        c = sys.stdin.read(1)
        match c:
          case "n":
            conf.doNUC = not conf.doNUC
          case "c":
            conf.useCalib = not conf.useCalib
      except IOError: pass
  finally:
    termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
    fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)


if __name__ == "__main__":
  main()
