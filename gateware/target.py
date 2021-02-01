import sys
from shutil import copyfile

from nmigen.sim import Simulator
from nmigen import *


from glasgowlib.i2c import I2CTargetTestbench, I2CTarget
from glasgowlib.registers import I2CRegisters
from glasgowlib.pads import Pads

from target_platform import TriggerPlatform
import registers_patch


from trigger import TriggerController, IdentRegisters, ResetController, ClockDivider


class TriggerTarget(Elaboratable):

    def __init__(self):
        self.registers = None
        self.enums = dict()

    def elaborate(self, platform):
        m = Module()

        if platform == None:
            m.submodules.i2c_target = I2CTargetTestbench()
            m.submodules.registers = registers_patch.apply(I2CRegisters(m.submodules.i2c_target))
            m.submodules.wall = ClockDivider(100)

            m.submodules.trig_ctrl  = TriggerController(m.submodules.registers, m.submodules.wall.strobe, 8, [])

        else:
            m.submodules.i2c_target = I2CTarget(platform.request("i2c"))
            m.submodules.registers = registers_patch.apply(I2CRegisters(m.submodules.i2c_target))

            ## Create a 1 kHz clock (1 ms) from 12 MHz source, so that register settings are in ms increments
            m.submodules.wall = ClockDivider(12000)
            
            ## Set I2C address 
            m.d.comb += m.submodules.i2c_target.address.eq(0b0001000)

            ## Create array of 8 reset pins.  CSI 0 thru 5, then aux2 & aux3
            resets = [("csi_rst",i) for i in range(6)] + [("aux",2), ("aux",3)]
            resets = [platform.request(name, num) for name,num in resets]

            ## Create array of 8 trigger pins.  CSI 0 thru 5, then aux0 & aux1
            triggers = [("csi_trig",i) for i in range(6)] + [("aux",0), ("aux",1)]
            triggers = [platform.request(name, num) for name,num in triggers]

            regs = m.submodules.registers
            m.submodules.ident      = IdentRegisters(regs, self.product_id, self.hardware_revision, self.gateware_revision)
            m.submodules.reset_ctrl = ResetController(regs, resets)
            m.submodules.trig_ctrl  = TriggerController(regs, m.submodules.wall.strobe, 8, triggers)

            self.enums["trigger_modes"] = m.submodules.trig_ctrl.modes

        self.registers = m.submodules.registers

        return m

    @property
    def product_id(self):
        return "CRZDGE"

    @property
    def hardware_revision(self):
        return 0

    @property
    def gateware_revision(self):
        return 0


class SimpleTests():

    def trigger(self):

        dut = TriggerTarget()
        sim = Simulator(dut)
        
        def process():
            
            ## Set trigger interval & duration
            yield dut.registers.regs_r[1].eq(8)
            yield dut.registers.regs_r[2].eq(2)

            # Simulate waiting before setting duration 
            # (trigger should not start yet)
            for i in range(200):
                yield

            # Start periodic trigger
            yield dut.registers.regs_r[0].eq(0x02)

            for i in range(2000):
                yield

            # Change the interval & duration values
            yield dut.registers.regs_r[1].eq(10)
            yield dut.registers.regs_r[2].eq(5)

            for i in range(2000):
                yield

        sim.add_sync_process(process)
        sim.add_clock(1e-5)

        with sim.write_vcd("trigger_test.vcd"):
            sim.run()

if __name__ == "__main__":

    if len(sys.argv) > 1:
        if sys.argv[1] == 'sim':
            sim = SimpleTests()
            sim.trigger()

        elif sys.argv[1] == 'ice':
            target = TriggerTarget()
            platform = TriggerPlatform()
            
            if len(sys.argv) > 2 and sys.argv[2] == 'flash':
                platform.build(target, do_program=True)
            else:
                platform.build(target)

            target.registers.display_table()
            target.registers.display_defines()
            # print(target.enums)
        