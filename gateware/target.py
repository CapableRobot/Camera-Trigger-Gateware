# Copyright 2021 Chris Osterwood for Capable Robot Components
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
from shutil import copyfile

from migen import *

from glasgowlib.i2c import I2CTargetTestbench, I2CTarget
from glasgowlib.registers import I2CRegisters
from glasgowlib.pads import Pads

from target_platform import TriggerPlatform
import registers_patch


from trigger import TriggerController, IdentRegisters, ClockDivider, Divider
from crossbar import CrossBarControl

class TriggerTarget(Module):
    sys_clk_freq = 12e6
    trigger_count = 4

    def __init__(self, platform=None):
        self.platform = platform
        self.registers = None
        self.enums = dict()

        if platform == 'sim':
            self.submodules.i2c_target = I2CTargetTestbench()
            self.submodules.registers = registers_patch.apply(I2CRegisters(self.i2c_target.dut))
            self.submodules.tick = ClockDivider(2)
            self.submodules.wall = Divider(self.tick.strobe, 2, 255)

            self.enable = Signal()
            self.submodules.trig_ctrl  = TriggerController(0, self.registers, self.wall.strobe, self.enable)

        else:
            self.submodules.i2c_pads  = Pads(self.platform.request("i2c"))
            self.submodules.i2c_target = I2CTarget(self.i2c_pads)
            self.submodules.registers = registers_patch.apply(I2CRegisters(self.i2c_target))
            
            ## Set I2C address 
            self.comb += self.i2c_target.address.eq(0b0001000)

            ## Create array of 8 reset pins.  CSI 0 thru 5, then aux2 & aux3
            resets = [("csi_rst",i) for i in range(6)] + [("aux",2), ("aux",3)]
            resets = [platform.request(name, num) for name,num in resets]

            ## Create array of 8 trigger pins.  CSI 0 thru 5, then aux0 & aux1
            triggers = [("csi_trig",i) for i in range(6)] + [("aux",0), ("aux",1)]
            triggers = [platform.request(name, num) for name,num in triggers]

            self.submodules.ident      = IdentRegisters(self.registers, self.product_id, self.hardware_revision, self.gateware_revision)

            self.registers.create("Trigger Count", default=self.trigger_count, ro=True)

            ## Create a 10 kHz clock (0.1 ms) from 12 MHz source
            self.submodules.tick = ClockDivider(1200)

            ## Create a adjustable divider on that 10 kHz clock.  
            ## Default is 10, to create a 1 ms strobe for the trigger. 
            reg_wall, _     = self.registers.create("Clock Divider", default=10, addr=20)
            self.submodules.wall = Divider(self.tick.strobe, 10, 255)
            self.comb += [
                self.wall.period.eq(reg_wall)
            ]

            reg_power, _  = self.registers.create("Power Control", default=0x01, addr=21)            
            camera_power = platform.request("camera_power", 0)

            self.comb += [
                camera_power.eq(reg_power[0])
            ]

            reg_enable, _  = self.registers.create("Trigger Enables", addr=60)
            trigger_outputs = []

            for num in range(self.trigger_count):
                trigger = TriggerController(num, 64+(num*8), self.registers, self.wall.strobe, reg_enable[num])

                setattr(self.submodules, "trigger{}".format(chr(0x41+num)), trigger)
                trigger_outputs.append(trigger.output)

            inputs = Array(trigger_outputs)
            self.submodules.crossbar = CrossBarControl(32, self.registers, inputs, triggers, resets)

            # self.enums["trigger_modes"] = self.trig_ctrl.modes

    @property
    def product_id(self):
        return "CRZDGE"

    @property
    def hardware_revision(self):
        return 0

    @property
    def gateware_revision(self):
        return 1

def test_trigger_control(dut):
    
    ## Set mode to interval
    yield dut.registers.regs_r[0].eq(2)

    ## Set phase
    yield dut.registers.regs_r[3].eq(2)

    ## Set trigger interval & duration
    yield dut.registers.regs_r[1].eq(8)

    yield dut.enable.eq(1)

    # Simulate waiting before setting duration 
    # (trigger should not start yet)
    for i in range(10):
        yield

    yield dut.registers.regs_r[2].eq(3)

    for i in range(100):
        yield

    yield dut.enable.eq(0)

    for i in range(20):
        yield

    yield dut.registers.regs_r[3].eq(4)
    yield dut.enable.eq(1)

    for i in range(100):
        yield

    # Change the interval & duration values
    yield dut.registers.regs_r[1].eq(16)
    yield dut.registers.regs_r[2].eq(5)

    for i in range(100):
        yield



class SimpleTests():

    def trigger(self):

        dut = TriggerTarget('sim')
        # dut.clock_domains.cd_sys = ClockDomain("sys")
        run_simulation(dut, test_trigger_control(dut), vcd_name="trigger_test.vcd")

if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1] == 'sim':
            sim = SimpleTests()
            sim.trigger()

        elif sys.argv[1] == 'ice':
            platform = TriggerPlatform()
            target = TriggerTarget(platform)
            
            if len(sys.argv) > 2 and sys.argv[2] == 'flash':
                platform.build(target, do_program=True)
            else:
                platform.build(target)

            target.registers.display_table()
            target.registers.display_defines()
            # print(target.enums)
        