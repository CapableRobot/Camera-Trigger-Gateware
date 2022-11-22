from migen import *

class IdentRegisters(Module):

    def __init__(self, registers, name, hardware_rev, gateware_rev):
        self.name = name
        self.hardware_rev = hardware_rev
        self.gateware_rev = gateware_rev

        registers.create("Product ID", len(self.name), default=self.name, ro=True)
        registers.create("Hardware Revision", 1, default=self.hardware_rev, ro=True)
        registers.create("Gateware Revision", 1, default=self.gateware_rev, ro=True)

        cameras = dict(
            CRZDGE=6,
            CRFDJ1=6,
            CRMHJN=5
        )

        registers.create("Camera Count", default=cameras[self.name], ro=True, addr=10)
        registers.create("GPIO Count", default=4, ro=True)

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

class Divider(Module):
    def __init__(self, strobe, period, maxperiod):
        counter = Signal(max=maxperiod)
        self.period  = Signal(max=maxperiod, reset=period)

        self.clock = Signal()
        self.strobe = Signal()

        self.sync += If(strobe,
            If(counter == 0,
                self.clock.eq(~self.clock),
                self.strobe.eq(1),
                counter.eq(self.period - 1),
            ).Else(
                counter.eq(counter - 1),
            )
        )

        ## Strobe reset is outside of parent strobe so that our strobe
        ## is 1 system clock long, instead of length of paree
        self.sync += If(self.strobe, self.strobe.eq(0))

TRIG_MODE = dict(
    stop = 0x00,
    idle = 0x01,
    interval = 0x02,
    oneshot = 0x03,
    constant = 0x04
)

TRIG_STATE = dict(
    off = 0x00,
    init = 0x01,
    wait = 0x02,
    active = 0x03
)

class Trigger(Module):

    def __init__(self, strobe, enable, width=8):
    
        self.trigger  = Signal()
        self.mode     = Signal(width)
        self.interval = Signal(width)
        self.duration = Signal(width)
        self.phase    = Signal(width)

        trigger_state = Signal(max=max(TRIG_STATE.values()))

        interval_counter = Signal(width)
        duration_counter = Signal(width)
        phase_counter    = Signal(width)

        return_mode = Signal(width)
        
        self.sync += If(enable,
            If(strobe,
                Case(self.mode, {
                    ## Make sure trigger is stopped (it might already be low)
                    TRIG_MODE['stop']: [
                        self.trigger.eq(0),
                        trigger_state.eq(TRIG_STATE['off'])
                    ],

                    ## Return state after a one-shot trigger
                    TRIG_MODE['idle']: [self.trigger.eq(self.trigger)],

                    ## Make sure we have a value (non zero) duration & interval before continuing
                    ## They are set outside of this module, and may not be set on the first clock edge
                    TRIG_MODE['interval']: [
                        If(self.duration != 0,
                            If(self.interval != 0, 
                                If(interval_counter == 0,
                                    duration_counter.eq(self.duration-1),   # Setup the trigger duration
                                    trigger_state.eq(TRIG_STATE['init']),   # Start the trigger
                                    interval_counter.eq(self.interval-1),   # Reset the trigger interval
                                ).Else(
                                    interval_counter.eq(interval_counter - 1),
                                )
                            )
                        )
                    ],

                    TRIG_MODE['oneshot']: [
                        If(self.duration != 0, 
                            If(trigger_state == TRIG_STATE['off'],
                                duration_counter.eq(self.duration-1),   # Setup the trigger duration
                                trigger_state.eq(TRIG_STATE['init']),   # Start the trigger 
                            )
                        )
                    ],

                    TRIG_MODE['constant']: [
                        If(trigger_state == TRIG_STATE['off'], 
                            trigger_state.eq(TRIG_STATE['init'])
                        )
                    ]

                }).makedefault(TRIG_MODE['idle'])
            )
        ).Else(
            self.trigger.eq(0),
            trigger_state.eq(TRIG_STATE['off']),
            interval_counter.eq(0),
            phase_counter.eq(0)
        )

        ## Count down the trigger duration once the trigger has been turned on
        self.sync += If(strobe,    
            If(self.trigger == 1,
                # Skip if in constant trigger mode (where trigger duration is ignored)
                If(self.mode != TRIG_MODE['constant'],                 
                    If(duration_counter == 0,                       
                        self.trigger.eq(0),                         # Stop the trigger 
                        trigger_state.eq(TRIG_STATE['off'])
                    ).Else(                             
                        duration_counter.eq(duration_counter - 1)   # Keep the trigger going
                    )
                )
            )
        )

        ## This is outside of 'strobe' so that it runs ~immediately after the trigger is initiated 
        ## (instead of waiting) for the next strobe edge.  This reduces latency when there is no
        ## phase delay.
        self.sync += [
            If(trigger_state == TRIG_STATE['init'],
                ## If a trigger has been entered (trigger_strobe == 2), check if there is a phase delay.
                ## If not, directly go to trigger being started
                ## If so, setup the phase count and enter the waiting state (trigger_strobe == 1)
                If(self.phase == 0,
                    self.trigger.eq(1),
                    trigger_state.eq(TRIG_STATE['active'])
                ).Else(
                    phase_counter.eq(self.phase - 1),
                    trigger_state.eq(TRIG_STATE['wait'])
                )
            )
        ]

        ## Count down the trigger's phase delay, if one has been set
        self.sync += If(strobe,
            ## Trigger phase delay has been set and we're in that period.
            ## Count down until the delay has been reached, then assert the trigger
            If(trigger_state == TRIG_STATE['wait'],
                If(phase_counter == 0,
                    self.trigger.eq(1),
                    trigger_state.eq(TRIG_STATE['active'])
                ).Else(
                    phase_counter.eq(phase_counter - 1),
                )
            )
        )

class TriggerController(Module):

    def __init__(self, idx, baseaddr, registers, strobe, enable):
        self.submodules.trigger = Trigger(strobe, enable)

        self.modes = TRIG_MODE

        ## TODO : support register widths != 8 bits
        reg_mode, _     = registers.create("Trigger{} Mode".format(idx), addr=baseaddr)
        reg_interval, _ = registers.create("Trigger{} Interval".format(idx), addr=baseaddr+1)
        reg_duration, _ = registers.create("Trigger{} Duration".format(idx), addr=baseaddr+2)
        reg_phase, _    = registers.create("Trigger{} Phase".format(idx), addr=baseaddr+3)

        self.comb += [
            self.trigger.mode.eq(reg_mode),
            self.trigger.interval.eq(reg_interval),
            self.trigger.duration.eq(reg_duration),
            self.trigger.phase.eq(reg_phase),
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
            