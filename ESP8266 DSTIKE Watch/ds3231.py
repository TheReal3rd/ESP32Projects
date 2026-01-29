from micropython import const
_DATETIME = const(0x00)
_STATUS   = const(0x0F)
_TEMP     = const(0x11)
def _bcd2dec(b):
    return (b >> 4) * 10 + (b & 0x0F)
def _dec2bcd(d):
    return (d // 10 << 4) | (d % 10)
class DS3231:
    def __init__(self, i2c, addr=0x68):
        self.i2c = i2c
        self.addr = addr
        self._buf = bytearray(7)
    def datetime(self, dt=None):
        if dt is None:
            self.i2c.readfrom_mem_into(self.addr, _DATETIME, self._buf)

            sec  = _bcd2dec(self._buf[0] & 0x7F)
            min  = _bcd2dec(self._buf[1])
            hour = _bcd2dec(self._buf[2] & 0x3F)
            day  = _bcd2dec(self._buf[4])
            mon  = _bcd2dec(self._buf[5])
            yr   = _bcd2dec(self._buf[6]) + 2000

            if self.osf():
                print("WARNING: Oscillator stop flag set")
                self._clear_osf()

            return (yr, mon, day, hour, min, sec)

        y, m, d, h, mi, s = dt
        self._buf[0] = _dec2bcd(s)
        self._buf[1] = _dec2bcd(mi)
        self._buf[2] = _dec2bcd(h)
        self._buf[3] = 0
        self._buf[4] = _dec2bcd(d)
        self._buf[5] = _dec2bcd(m)
        self._buf[6] = _dec2bcd(y - 2000)

        self.i2c.writeto_mem(self.addr, _DATETIME, self._buf)
        self._clear_osf()
    def osf(self):
        return bool(self.i2c.readfrom_mem(self.addr, _STATUS, 1)[0] & 0x80)
    def _clear_osf(self):
        s = self.i2c.readfrom_mem(self.addr, _STATUS, 1)[0]
        self.i2c.writeto_mem(self.addr, _STATUS, bytes([s & 0x7F]))
    def temperature(self):
        t = self.i2c.readfrom_mem(self.addr, _TEMP, 2)
        return t[0] + (t[1] >> 6) * 0.25


