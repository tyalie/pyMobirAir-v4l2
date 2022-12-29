# Python user space driver for MobIR AIR Thermal camera

This is a user space driver for the USB-C [Guide MobIR Air][mobirair-product-page].
It uses `libusb` and [`v4l2loopback`][v4l2loopback] to realize this.

> Disclaimer: Most of the algorithms here have been reverse engineered from
> the MobIR Android app. (I'm an EU citizen and this is a tool to increase
> compatibility with the named thermal camera)


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

Afterwards one can start the driver with `./src/main.py -l /dev/videoX`. It needs to be 
noted here, that the script requires the thermal camera to be already connected to the 
host device.

The `/dev/videoX` feed is a Y16 RAW feed, with a single pixel being Kelvin values *
100.


### Notes

1. A cold start of the camera requires about a minute until the temperature stabilizes
   consistently. Before that point the measured temperature will fall rapidly into
   impossible ranges (e.g. negative °C) and return into a feasible range during each
   calibration.

2. The code is not guaranteed to be bug-free. For one, it does not handle edge error 
   cases correctly, but will instead crash. On the other the resulting temperatures
   could very well be completely off. The algorithms in `MobirAirTempUtils` have been
   tested against the original app and seem to be correct. But this is not guaranteed
   for the parameters needed in these formulas.

[mobirair-product-page]: https://www.guideir.com/products/mobileaccessories/mobirair/data_300.html
[v4l2loopback]: https://github.com/umlaeute/v4l2loopback
