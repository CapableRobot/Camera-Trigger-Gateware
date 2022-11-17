from migen import *

class IdentRegisters(Module):

    def __init__(self, registers, name, hardware_rev, gateware_rev, reserved=16):
        self.name = name
        self.hardware_rev = hardware_rev
        self.gateware_rev = gateware_rev
        self.reserved = reserved

        registers.create("Product ID", len(self.name), default=self.name, ro=True)
        registers.create("Hardware Revision", 1, default=self.hardware_rev, ro=True)
        registers.create("Gateware Revision", 1, default=self.gateware_rev, ro=True)
        registers.create("Reserved", self.reserved-len(self.name)-2, default=0, ro=True)

class ClockDivider(Module):
    def __init__(self, maxperiod):
        counter = Signal(max=maxperiod)
        period  = Signal(max=maxperiod)

        self.clock = Signal()
        self.strobe = Signal()

        self.comb += period.eq(maxperiod-1)

        self.sync += If(counter == 0,
                            self.clock.eq(~self.clock),
                            self.strobe.eq(1),
                            counter.eq(period),
                        ).Else(
                            self.strobe.eq(0),
                            counter.eq(counter - 1),
                        )

TRIG_MODE = dict(
    stop = 0x00,
    idle = 0x01,
    interval = 0x02,
    oneshot = 0x03,
    constant = 0x04
)

class Trigger(Module):

    def __init__(self, strobe, width):
    
        self.trigger  = Signal()
        self.mode     = Signal(width)
        self.interval = Signal(width)
        self.duration = Signal(width)

        interval_counter = Signal(width)
        duration_counter = Signal(width)
        
        self.sync += If(strobe,
            Case(self.mode, {
                ## Make sure trigger is stopped (it might already be low)
                TRIG_MODE['stop']: [self.trigger.eq(0)],

                ## Return state after a one-shot trigger
                TRIG_MODE['idle']: [self.trigger.eq(self.trigger)],

                ## Make sure we have a value (non zero) duration & interval before continuing
                ## They are set outside of this module, and may not be set on the first clock edge
                TRIG_MODE['interval']: [
                    If(self.duration != 0,
                        If(self.interval != 0, 
                            If(interval_counter == 0,
                                duration_counter.eq(self.duration-1),   # Setup the trigger duration
                                self.trigger.eq(1),                     # Start the trigger
                                interval_counter.eq(self.interval-1),   # Reset the trigger interval
                            ).Else(
                                interval_counter.eq(interval_counter - 1),
                            )
                        )
                    )
                ],

                TRIG_MODE['oneshot']: [
                    If(self.duration != 0, 
                        duration_counter.eq(self.duration-1),   # Setup the trigger duration
                        self.trigger.eq(1),                     # Start the trigger 
                    )
                ],

                TRIG_MODE['constant']: [self.trigger.eq(1)]

            }).makedefault(TRIG_MODE['idle']),

            If(self.trigger == 1,
                # Skip if in constant trigger mode (where trigger duration is ignored)
                If(self.mode != TRIG_MODE['constant'],                 
                    If(duration_counter == 0,                       
                        self.trigger.eq(0)                          # Stop the trigger 
                    ).Else(                             
                        duration_counter.eq(duration_counter - 1)   # Keep the trigger going
                    )
                )
            )
        )

class ResetController(Module):

    def __init__(self, registers, reset_pins):
        assert len(reset_pins) == 8
        register, _ = registers.create("Reset")

        for i in range(len(reset_pins)):
            self.comb  += reset_pins[i].eq(register[i])

class TriggerController(Module):

    def __init__(self, registers, strobe, width):
        self.submodules.trigger = Trigger(strobe, width)

        self.modes = TRIG_MODE

        ## TODO : support register widths != 8 bits
        reg_mode, _     = registers.create("Trigger Mode")
        reg_interval, _ = registers.create("Trigger Interval")
        reg_duration, _ = registers.create("Trigger Duration")
        reg_mask, _     = registers.create("Trigger Mask")

        self.comb += [
            self.trigger.mode.eq(reg_mode),
            self.trigger.interval.eq(reg_interval),
            self.trigger.duration.eq(reg_duration),
        ]

        self.sync += [
            If(strobe,
                ## We've started the trigger, can now return to IDLE mode
                If(reg_mode == TRIG_MODE['oneshot'],
                    If(self.trigger.trigger == 1,
                        reg_mode.eq(TRIG_MODE['idle']) 
                    )
                ),
                ## We're IDLE and trigger has stopped, go to STOP
                If(reg_mode == TRIG_MODE['idle'],
                    If(self.trigger.trigger == 0,
                        reg_mode.eq(TRIG_MODE['stop'])
                    )
                )
            )
        ]

        self.output = self.trigger.trigger
            