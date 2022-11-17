# Copyright 2022 Chris Osterwood for Capable Robot Components
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

from migen import *
from migen.fhdl import verilog
from migen.fhdl.bitcontainer import bits_for

class CrossBarCell(Module):

    def __init__(self, inputs, selection, oe, default, invert):

        mux_out = Signal()
        self.output = Signal()

        self.sync += mux_out.eq(inputs[selection[0:]])
        self.comb += self.output.eq(
            Mux(oe, 
                Mux(invert, ~mux_out, mux_out), 
                default)
            )

class CrossBar(Module):

    def __init__(self, inputs, outputs):
        self.crossbars = []
        self.controls = []

        for i in range(len(outputs)):

            control = Signal(8)
            self.controls.append(control)

            oe        = control[7]
            default   = control[6]
            invert    = control[5]
            selection = control[0:bits_for(len(inputs))]

            if len(selection) > 5:
                raise ValueError("Input length exceeds control range")
    
            cell = CrossBarCell(inputs, selection, oe, default, invert)
            self.crossbars.append(cell)

            self.submodules += cell
            self.comb  += outputs[i].eq(self.crossbars[i].output)


class CrossBarControl(Module):

    def __init__(self, registers, inputs, bank_a, bank_b):

        a_count = len(bank_a)
        b_count = len(bank_b)
        outputs = Signal(a_count + b_count)

        self.submodules.crossbar = CrossBar(inputs, outputs)

        for i in range(a_count):
            ctrl, _ = registers.create("Crossbar A{}".format(i), default=0b0100_0000)

            self.comb += self.crossbar.controls[i].eq(ctrl),
            self.comb += bank_a[i].eq(outputs[i])
        
        for i in range(b_count):
            ctrl, _ = registers.create("Crossbar B{}".format(i), default=0b0100_0000)

            self.comb += self.crossbar.controls[i + a_count].eq(ctrl),
            self.comb += bank_b[i].eq(outputs[i + a_count])

