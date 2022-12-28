# Python user space driver for MobIR AIR Thermal camera

This is a user space driver for the USB-C [Guide MobIR Air][mobirair-product-page].
It uses `libusb` and [`v4l2loopback`][v4l2loopback] to realize this.

> Disclaimer: Most of the algorithms here have been reverse engineered from
> the MobIR Android app.


## Usage

First step is to create a v4l2 loopback device, this can be done during module
loading or with the `v4l2loopback-ctl` command.

```bash
# enable v4l2loopback with one device
modprobe v4l2loopback devices=1
```

The next step is to configure your loopback video device (`/dev/video*`) in the app,
and install all dependencies (see `requirements.txt`).

```bash
python3 -m pip install -r requirements.txt
```

Afterwards one can start the driver with `./src/main.py`. It needs to be noted here,
that the script requires the thermal camera to be already connected to the host device.

The `/dev/videoX` feed is a Y16 RAW feed, with a single pixel being Kelvin values *
100.

[mobirair-product-page]: https://www.guideir.com/products/mobileaccessories/mobirair/data_300.html
[v4l2loopback]: https://github.com/umlaeute/v4l2loopback
