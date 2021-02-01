from nmigen import *

class IdentRegisters(Elaboratable):

    def __init__(self, registers, name, hardware_rev, gateware_rev, reserved=16):
        self._registers = registers
        self.name = name
        self.hardware_rev = hardware_rev
        self.gateware_rev = gateware_rev
        self.reserved = reserved

    def elaborate(self, platform):
        m = Module()

        self._registers.append(m, "Product ID", len(self.name), default=self.name, ro=True)
        self._registers.append(m, "Hardware Revision", 1, default=self.hardware_rev, ro=True)
        self._registers.append(m, "Gateware Revision", 1, default=self.gateware_rev, ro=True)
        self._registers.append(m, "Reserved", self.reserved-len(self.name)-2, default=0, ro=True)

        return m


class ClockDivider(Elaboratable):
    def __init__(self, maxperiod):
        self.maxperiod = maxperiod

        self.counter = Signal(range(maxperiod))
        self.period  = Signal(range(maxperiod))

        self.clock = Signal()
        self.strobe = Signal()

    def elaborate(self, platform):
        m = Module()

        m.d.comb += self.period.eq(self.maxperiod-1)

        with m.If(self.counter == 0):
            m.d.sync += [
                self.clock.eq(~self.clock),
                self.strobe.eq(1),
                self.counter.eq(self.period)
            ]
        with m.Else():
            m.d.sync += [
                self.strobe.eq(0),
                self.counter.eq(self.counter - 1)
            ]

        return m

TRIG_MODE = dict(
    stop = 0x00,
    idle = 0x01,
    interval = 0x02,
    oneshot = 0x03,
    constant = 0x04
)

class Trigger(Elaboratable):

    def __init__(self, strobe, width):
        self.strobe = strobe
        self.width = width

        self.trigger  = Signal()
        self.mode     = Signal(width, reset=TRIG_MODE['idle'])
        self.interval = Signal(width)
        self.duration = Signal(width)

    def elaborate(self, platform):
        m = Module()
        
        interval_counter = Signal(self.width)
        duration_counter = Signal(self.width)

        with m.If(self.strobe):
            with m.Switch(self.mode):
                ## Make sure trigger is stopped (it might already be low)
                with m.Case(TRIG_MODE['stop']): 
                    m.d.sync += self.trigger.eq(0)

                ## Return state after a one-shot trigger
                with m.Case(TRIG_MODE['idle']): 
                    m.d.sync += self.trigger.eq(self.trigger)

                ## Make sure we have a value (non zero) duration & interval before continuing
                ## They are set outside of this module, and may not be set on the first clock edge
                with m.Case(TRIG_MODE['interval']): 
                    with m.If((self.duration != 0) & (self.interval != 0)):
                        with m.If(interval_counter == 0):
                            m.d.sync += [
                                duration_counter.eq(self.duration-1),   # Setup the trigger duration
                                self.trigger.eq(1),                     # Start the trigger
                                interval_counter.eq(self.interval-1)    # Reset the trigger interval
                            ]
                        with m.Else():
                            m.d.sync += interval_counter.eq(interval_counter - 1)

                with m.Case(TRIG_MODE['oneshot']): 
                    with m.If(self.duration != 0): 
                        m.d.sync += [
                            duration_counter.eq(self.duration-1),   # Setup the trigger duration
                            self.trigger.eq(1)                      # Start the trigger 
                        ]
                
                with m.Case(TRIG_MODE['constant']):
                    m.d.sync += self.trigger.eq(1)

            
            # Skip if in constant trigger mode (where trigger duration is ignored)
            with m.If((self.trigger == 1) & (self.mode != TRIG_MODE['constant'])):
                with m.If(duration_counter == 0):
                    # Stop the trigger 
                    m.d.sync += self.trigger.eq(0)                  
                with m.Else():
                    # Keep the trigger going
                    m.d.sync += duration_counter.eq(duration_counter - 1)   
            
        return m

class ResetController(Elaboratable):

    def __init__(self, registers, reset_pins):
        assert len(reset_pins) == 8
        self.reset_pins = reset_pins
        self._registers = registers

    def elaborate(self, platform):
        m = Module()

        reg, _ = self._registers.append(m, "Reset Mask")

        for i in range(len(self.reset_pins)):
            m.d.comb += self.reset_pins[i].eq(reg[i])

        return m

class TriggerController(Elaboratable):

    def __init__(self, registers, strobe, width, trigger_pins):
        self._registers = registers

        self.strobe = strobe
        self.width = width
        self.trigger_pins = trigger_pins

        self.modes = TRIG_MODE

    def elaborate(self, platform):
        m = Module()

        trigger = Trigger(self.strobe, self.width)
        m.submodules.trigger = trigger

        reg_mode, _     = self._registers.append(m, "Trigger Mode")
        reg_interval, _ = self._registers.append(m, "Trigger Interval")
        reg_duration, _ = self._registers.append(m, "Trigger Duration")
        reg_mask, _     = self._registers.append(m, "Trigger Mask")


        m.d.comb += [
            trigger.mode.eq(reg_mode),
            trigger.interval.eq(reg_interval),
            trigger.duration.eq(reg_duration),
        ]

        with m.If(self.strobe):
                ## We've started the trigger, can now return to IDLE mode
                with m.If((reg_mode == TRIG_MODE['oneshot']) & (trigger.trigger == 1)):
                    m.d.sync += reg_mode.eq(TRIG_MODE['idle']) 
            
        with m.Else():
                ## We've IDLE and trigger has stopped, go to STOP
                with m.If((reg_mode == TRIG_MODE['idle']) & (trigger.trigger == 0)):
                    m.d.sync += reg_mode.eq(TRIG_MODE['stop'])
            
        ## Apply mask between internal trigger signal and hardware pins
        for i in range(len(self.trigger_pins)):
            m.d.comb  += self.trigger_pins[i].eq(reg_mask[i] & trigger.trigger)

        return m