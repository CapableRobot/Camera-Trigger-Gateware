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

from migen.build.generic_platform import *
from migen.build.lattice import LatticePlatform
from migen.build.lattice.programmer import IceStormProgrammer

class TriggerPlatform(LatticePlatform):
    default_clk_name = "clk12"
    default_clk_period = 83.333

    resources   = [
        ("clk12", 0, Pins("35"), IOStandard("LVCMOS33")),

        ("led",    0, Pins("37"), IOStandard("LVCMOS33")),
        ("led",    1, Pins("11"), IOStandard("LVCMOS33")),
        ("led0",   0, Pins("37"), IOStandard("LVCMOS33")),
        ("led1",   0, Pins("11"), IOStandard("LVCMOS33")),

        ("i2c", 0,
            Subsignal("scl", Pins("4")),
            Subsignal("sda", Pins("3")),
            IOStandard("LVCMOS18")),

        ("aux", 0, Pins("18"), IOStandard("LVCMOS33")),
        ("aux", 1, Pins("19"), IOStandard("LVCMOS33")),
        ("aux", 2, Pins("20"), IOStandard("LVCMOS33")),
        ("aux", 3, Pins("21"), IOStandard("LVCMOS33")),

        ("camera_power", 0, Pins("13"), IOStandard("LVCMOS33")),
        ("camera_power_3v3", 0, Pins("13"), IOStandard("LVCMOS33")),

        ("csi_rst", 0, Pins("34"), IOStandard("LVCMOS33")),
        ("csi_rst", 1, Pins("38"), IOStandard("LVCMOS33")),
        ("csi_rst", 2, Pins("43"), IOStandard("LVCMOS33")),
        ("csi_rst", 3, Pins("31"), IOStandard("LVCMOS33")),
        ("csi_rst", 4, Pins("27"), IOStandard("LVCMOS33")),
        ("csi_rst", 5, Pins("25"), IOStandard("LVCMOS33")),

        ("csi_trig", 0, Pins("32"), IOStandard("LVCMOS33")),
        ("csi_trig", 1, Pins("36"), IOStandard("LVCMOS33")),
        ("csi_trig", 2, Pins("42"), IOStandard("LVCMOS33")),
        ("csi_trig", 3, Pins("28"), IOStandard("LVCMOS33")),
        ("csi_trig", 4, Pins("26"), IOStandard("LVCMOS33")),
        ("csi_trig", 5, Pins("23"), IOStandard("LVCMOS33")),
    ]

    connectors = []

    def __init__(self):
        LatticePlatform.__init__(self, "ice40-up5k-sg48", self.resources, self.connectors, toolchain="icestorm")

    def create_programmer(self):
        return IceStormProgrammer()
