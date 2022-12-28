class MobirAirTempUtils:
  def __init__(self, state: "MobirAirState") -> None:
    self._state = state

  def getY16byShutterTemp(self, shutterTemp: int):
    return self._state.currCurve[int(shutterTemp * 10)]

  @staticmethod
  def getFpaTemp(fpaTemp: int, module_tp: int) -> float:
    """ realtimeTfpa from the camera itself isn't the value
    that is further used, but instead a transformed value of it.
    The calculation depends on the moduleTP number.

    The numbers here are taken directly from the app.
    """

    if module_tp not in [0x2, 0x3]:
      v_ = (33818e4 - fpaTemp * 18181) / 1e3
    else:
      v_ = (fpaTemp * -0.0201 + 371.29) * 100

    return int(v_) / 100

  @staticmethod
  def getParamTemp(temp: int) -> float:
    t0 = 127.361304901973
    t1 = -0.018218076216914 * temp
    t2 =  1.218402729E-6 * temp**2
    t3 = -4.0235E-11 * temp**3
    poly = t3 + t2 + t1 + t0
    return int(poly * 100) / 100
