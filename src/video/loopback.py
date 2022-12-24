from pathlib import Path
import time
import fcntl
import v4l2py.raw as vraw


def get_format(width, height) -> vraw.v4l2_format:
  f = vraw.v4l2_format()
  f.type = vraw.V4L2_BUF_TYPE_VIDEO_OUTPUT
  f.fmt.pix.pixelformat = vraw.V4L2_PIX_FMT_Y16
  f.fmt.pix.width = width
  f.fmt.pix.height = height
  f.fmt.pix.field = vraw.V4L2_FIELD_NONE
  f.fmt.pix.bytesperline = width * 2
  f.fmt.pix.sizeimage = width * height * 2
  f.fmt.pix.colorspace = vraw.V4L2_COLORSPACE_RAW
  return f


def main(device: Path | str):
  stream = open(device, "wb")

  i = 0
  while True:
    a = b"\x00" * i * 2
    b = b"\x00" * (100 * 100 - i - 1) * 2
    stream.write(a + b"\xff\xff" + b)
    stream.flush()
    time.sleep(1/30)
    i = (i + 1) % (100 * 100)


def create_loopback(device: Path | str, width: int, height: int):
  stream = open(device, "wb")

  # set video format
  format = get_format(width, height)
  fcntl.ioctl(stream, vraw.VIDIOC_S_FMT, format)

  return stream

