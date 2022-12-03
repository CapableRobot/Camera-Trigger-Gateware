import logging
import time
from smbus2 import SMBus, i2c_msg

DEVICE_ADDRESS = 0x08
DELAY = 0.001
I2CBUS = 2

def const(value):
    return value

_REG_PRODUCT_ID           = const(0x00)
_REG_HARDWARE_REVISION    = const(0x06)
_REG_GATEWARE_REVISION    = const(0x07)
_REG_CAMERA_COUNT         = const(0x0A)
_REG_GPIO_COUNT           = const(0x0B)
_REG_TRIGGER_COUNT        = const(0x0C)
_REG_CLOCK_DIVIDER        = const(0x14)
_REG_POWER_CONTROL        = const(0x15)
_REG_POWER_SENSE          = const(0x16)
_REG_TRIGGER_ENABLES      = const(0x3C)
_REG_TRIGGER0_MODE        = const(0x40)
_REG_TRIGGER0_INTERVAL    = const(0x41)
_REG_TRIGGER0_DURATION    = const(0x42)
_REG_TRIGGER0_DELAY       = const(0x43)
_REG_TRIGGER1_MODE        = const(0x48)
_REG_TRIGGER1_INTERVAL    = const(0x49)
_REG_TRIGGER1_DURATION    = const(0x4A)
_REG_TRIGGER1_DELAY       = const(0x4B)
_REG_TRIGGER2_MODE        = const(0x50)
_REG_TRIGGER2_INTERVAL    = const(0x51)
_REG_TRIGGER2_DURATION    = const(0x52)
_REG_TRIGGER2_DELAY       = const(0x53)
_REG_TRIGGER3_MODE        = const(0x58)
_REG_TRIGGER3_INTERVAL    = const(0x59)
_REG_TRIGGER3_DURATION    = const(0x5A)
_REG_TRIGGER3_DELAY       = const(0x5B)
_REG_CROSSBAR_A0          = const(0x20)
_REG_CROSSBAR_A1          = const(0x21)
_REG_CROSSBAR_A2          = const(0x22)
_REG_CROSSBAR_A3          = const(0x23)
_REG_CROSSBAR_A4          = const(0x24)
_REG_CROSSBAR_A5          = const(0x25)
_REG_CROSSBAR_A6          = const(0x26)
_REG_CROSSBAR_A7          = const(0x27)
_REG_CROSSBAR_B0          = const(0x28)
_REG_CROSSBAR_B1          = const(0x29)
_REG_CROSSBAR_B2          = const(0x2A)
_REG_CROSSBAR_B3          = const(0x2B)
_REG_CROSSBAR_B4          = const(0x2C)
_REG_CROSSBAR_B5          = const(0x2D)
_REG_CROSSBAR_B6          = const(0x2E)
_REG_CROSSBAR_B7          = const(0x2F)

TRIG_MODE = dict(
    stop = 0x00,
    idle = 0x01,
    interval = 0x02,
    oneshot = 0x03,
    constant = 0x04
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
logger.addHandler(ch)

def set_bit(value, bit):
    return value | (1<<bit)

def clear_bit(value, bit):
    return value & ~(1<<bit)

def get_bit(value, bit):
    return (value & (1<<bit)) > 0 


def write_register(address, value):
    logger.debug("W " + hex(address) + " " + "".join("{:02x}".format(x) for x in [value]))

    msg_set = i2c_msg.write(DEVICE_ADDRESS, [address, value])

    with SMBus(I2CBUS) as bus:
        bus.i2c_rdwr(msg_set)


def read_register(address, length=1):

    result = []
    tmp = bytearray(1)

    with SMBus(I2CBUS) as bus:
        for idx in range(length):
            msg_set = i2c_msg.write(DEVICE_ADDRESS, [address+idx])
            msg_get = i2c_msg.read(DEVICE_ADDRESS, 1)
            bus.i2c_rdwr(msg_set, msg_get)

            result.append(list(msg_get)[0])

    logger.debug("R " + hex(address) + " " + "".join("{:02x}".format(x) for x in result))

    if length == 1:
        return result[0]
    else:
        return bytearray(result)


class Pin:

    ENABLE_BIT  = 7
    DEFAULT_BIT = 6
    INVERT_BIT  = 5

    def __init__(self, name, address):
        self.name = name
        self.address = address

        self.fetch()

    def fetch(self):
        self.setting = read_register(self.address)

    def reset(self):
        reg = 0b0100_0000
        write_register(self.address, reg)
        self.setting = reg

    @property
    def enable(self):
        return get_bit(self.setting, self.ENABLE_BIT)

    @enable.setter
    def enable(self, value):
        reg = self.setting

        if value or value > 0:
            reg = set_bit(reg, self.ENABLE_BIT)
        else:
            reg = clear_bit(reg, self.ENABLE_BIT)

        if reg != self.setting:
            write_register(self.address, reg)
            self.setting = reg


    @property
    def default(self):
        return get_bit(self.setting, self.DEFAULT_BIT)

    @default.setter
    def default(self, value):
        reg = self.setting

        if value or value > 0:
            reg = set_bit(reg, self.DEFAULT_BIT)
        else:
            reg = clear_bit(reg, self.DEFAULT_BIT)

        if reg != self.setting:
            write_register(self.address, reg)
            self.setting = reg


    @property
    def invert(self):
        return get_bit(self.setting, self.INVERT_BIT)

    @invert.setter
    def invert(self, value):
        reg = self.setting

        if value or value > 0:
            reg = set_bit(reg, self.INVERT_BIT)
        else:
            reg = clear_bit(reg, self.INVERT_BIT)

        if reg != self.setting:
            write_register(self.address, reg)
            self.setting = reg


    @property
    def trigger(self):
        if self.invert:
            return False
        else:
            return self.setting & 0b0001_1111

    @trigger.setter
    def trigger(self, value):
        selected = value & 0b0001_1111

        reg = self.setting & 0b1110_0000
        reg = set_bit(reg, self.ENABLE_BIT)
        reg = reg | selected

        if reg != self.setting:
            write_register(self.address, reg)
            self.setting = reg

    @property
    def inverted_trigger(self):
        if self.invert:
            return self.setting & 0b0001_1111
        else:
            return False

    @inverted_trigger.setter
    def inverted_trigger(self, value):
        selected = value & 0b0001_1111

        reg = self.setting & 0b1110_0000
        reg = set_bit(reg, self.ENABLE_BIT)
        reg = set_bit(reg, self.INVERT_BIT)
        reg = reg | selected

        if reg != self.setting:
            write_register(self.address, reg)
            self.setting = reg

class Trigger:

    def __init__(self, index):
        self.index = index
        self._offset = index * (_REG_TRIGGER1_MODE - _REG_TRIGGER0_MODE)

    def offset(self, address):
        return address + self._offset

    @property
    def mode(self):
        value = read_register(self.offset(_REG_TRIGGER0_MODE))

        for key, v in TRIG_MODE.items():
            if v == value:
                return key

        return None

    @mode.setter
    def mode(self, name):
        write_register(self.offset(_REG_TRIGGER0_MODE), TRIG_MODE[name])

    @property
    def duration(self):
        return read_register(self.offset(_REG_TRIGGER0_DURATION))

    @duration.setter
    def duration(self, value):
        write_register(self.offset(_REG_TRIGGER0_DURATION), value)

    @property
    def interval(self):
        return read_register(self.offset(_REG_TRIGGER0_INTERVAL))

    @interval.setter
    def interval(self, value):
        write_register(self.offset(_REG_TRIGGER0_INTERVAL), value)

    @property
    def delay(self):
        return read_register(self.offset(_REG_TRIGGER0_DELAY))

    @delay.setter
    def delay(self, value):
        write_register(self.offset(_REG_TRIGGER0_DELAY), value)

class TriggerController:

    def __init__(self):
        self.enables = read_register(_REG_TRIGGER_ENABLES)
        self._triggers = dict()
        self._pins = dict()

    def ident(self):
        data = read_register(0x00, 8)
        mpn = ''.join([chr(v) for v in data[0:6]])
        hwr = data[6]
        gwr = data[7]
        
        return mpn, hwr, gwr    

    def trigger(self, index):
        if index not in self._triggers.keys():
            self._triggers[index] = Trigger(index)

        return self._triggers[index]        

    def pin(self, name):
        if name not in self._pins.keys():
            if name[0] == 'A':
                self._pins[name] = Pin(name, _REG_CROSSBAR_A0 + int(name[1]))
            if name[0] == 'B':
                self._pins[name] = Pin(name, _REG_CROSSBAR_B0 + int(name[1]))

        return self._pins[name]

    def enable(self, mask=0xFF):
        if mask != self.enables:
            write_register(_REG_TRIGGER_ENABLES, mask)
            self.enables = mask

    def disable(self):
        reg = 0

        if reg != self.enables:
            write_register(_REG_TRIGGER_ENABLES, reg)
            self.enables = reg

    @property
    def clock_divider(self):
        return read_register(_REG_CLOCK_DIVIDER)

    @clock_divider.setter
    def clock_divider(self, value):
        write_register(_REG_CLOCK_DIVIDER, value)


if __name__ == "__main__":

    ctrl = TriggerController()
    print(ctrl.ident())

    ctrl.trigger(0).interval = 20
    ctrl.trigger(0).duration = 10

    ctrl.trigger(1).interval = 20
    ctrl.trigger(1).duration = 10
    ctrl.trigger(1).delay = 5

    a0 = ctrl.pin("A0")
    a1 = ctrl.pin("A1")

    a0.trigger = 0
    a1.trigger = 1
    # a1.invert = True

    ctrl.trigger(0).mode = "interval"
    ctrl.trigger(1).mode = "interval"

    ctrl.enable(mask=3)

    time.sleep(0.05)

    ctrl.disable()

    ctrl.trigger(0).mode = "stop"
    ctrl.trigger(1).mode = "stop"

    a0.reset()
    a1.reset()