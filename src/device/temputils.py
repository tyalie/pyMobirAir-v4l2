import numpy as np

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

  def y16toTemp(self, y16: np.ndarray):
    """Convert y16 raw data frame into temperatures (°C)
    """
    param = self._state.measureParam

    rawTemp = y16 - np.average(self._state.shutterFrame)

    _temp = rawTemp - int((
      (param.kj / 100) * (param.realtimeTlens - param.lastShutterTlens)
    ))

    _tcurr = self.calcSingleCurveTempArr(self._state.currCurve, _temp)
    _tnear = self.calcSingleCurveTempArr(self._state.nearCurve, _temp)

    _jwbArr = self._state.jwbTabArrShort
    _i = param.currChangeRTfpgIdx
    if _i == 0:
        _t1 = param.realtimeTfpa * 100 - _jwbArr[0]
        _t2 = _jwbArr[1] - param.realtimeTfpa * 100
    elif self._state.jwbTabNumber - 1 == _i:
        _t1 = _jwbArr[_i - 1] - param.realtimeTfpa * 100
        _t2 = param.realtimeTfpa * 100 - _jwbArr[_i]
    else:
        _t1 = _jwbArr[_i] - param.realtimeTfpa * 100
        _t2 = param.realtimeTfpa * 100 - _jwbArr[_i - 1]

    _td = _t1 + _t2
    return _tcurr * (1 - _t1 / _td) + _tnear * (1 - _t2 / _td)

  def calcSingleCurveTempArr(self, curveArr: np.ndarray, values: np.ndarray):
    param = self._state.measureParam

    _idx = int(param.realtimeTshutter * 10 + 200)
    assert 0 < _idx and _idx < len(curveArr), f"{_idx} is out of bounds"
    cal_val = curveArr[_idx]

    deltaTfpaRef = param.realtimeTfpa - param.tref
    deltaTfpaK2 = (param.realtimeTfpa - param.lastShutterTfpa) * param.k2
    deltaTlens = param.realtimeTlens - param.lastShutterTlens

    _raw = deltaTfpaRef * values
    k1raw = ((_raw * param.k1) / 3 * 100).astype("i2")

    k5dTlens  = deltaTlens    * param.k5
    k4dTlens2 = deltaTlens**2 * param.k4
    k3dTlens3 = deltaTlens**3 * param.k3

    _noidea0 = k3dTlens3 / 100 \
      + k4dTlens2 / 100 \
      + k5dTlens \
      + deltaTfpaK2

    _noidea1 = values \
      + (_raw * param.k0 * deltaTfpaRef * 1e4) \
      + ((k1raw >> 0x19) - np.sign(k1raw)) \
      + _noidea0 // 100_000

    _v3 = np.clip(_noidea1, -0x8000, 0x7fff)
    _v4 = _v3 * param.kf
    _v5 = _v4 // 1e4 + cal_val

    _v6 = np.clip(_v5, -0x8000, 0x7fff)

    _cache = np.clip(_v6, curveArr[0], curveArr[-1])

    i = curveArr.searchsorted(_cache, side="left")
    curve_temp = i / 10.0 - 20

    return curve_temp + param.b / 100

