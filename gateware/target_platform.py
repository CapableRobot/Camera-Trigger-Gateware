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

from nmigen.build import *
from nmigen.vendor.lattice_ice40 import *

##
## https://github.com/nmigen/nmigen-boards/blob/master/nmigen_boards/resources/memory.py
##
def SPIFlashResources(*args, cs_n, clk, copi, cipo, wp_n=None, hold_n=None,
                      conn=None, attrs=None):
    resources = []

    io_all = []
    if attrs is not None:
        io_all.append(attrs)
    io_all.append(Subsignal("cs",  PinsN(cs_n, dir="o", conn=conn)))
    io_all.append(Subsignal("clk", Pins(clk, dir="o", conn=conn, assert_width=1)))

    io_1x = list(io_all)
    io_1x.append(Subsignal("copi", Pins(copi, dir="o", conn=conn, assert_width=1)))
    io_1x.append(Subsignal("cipo", Pins(cipo, dir="i", conn=conn, assert_width=1)))
    if wp_n is not None and hold_n is not None:
        io_1x.append(Subsignal("wp",   PinsN(wp_n,   dir="o", conn=conn, assert_width=1)))
        io_1x.append(Subsignal("hold", PinsN(hold_n, dir="o", conn=conn, assert_width=1)))
    resources.append(Resource.family(*args, default_name="spi_flash", ios=io_1x,
                                     name_suffix="1x"))

    io_2x = list(io_all)
    io_2x.append(Subsignal("dq", Pins(" ".join([copi, cipo]), dir="io", conn=conn,
                                      assert_width=2)))
    resources.append(Resource.family(*args, default_name="spi_flash", ios=io_2x,
                                     name_suffix="2x"))

    if wp_n is not None and hold_n is not None:
        io_4x = list(io_all)
        io_4x.append(Subsignal("dq", Pins(" ".join([copi, cipo, wp_n, hold_n]), dir="io", conn=conn,
                                          assert_width=4)))
        resources.append(Resource.family(*args, default_name="spi_flash", ios=io_4x,
                                         name_suffix="4x"))

    return resources

## Pin mapping
## PIN  NAME
##
## 4      SCL
## 2      -
## 47     SIG_RST
## 45     SIG_MCLK (not easy to use on TX2)
## 3      SDA
## 48     SIG_INTR (not easy to use on TX2)
## 46     SIG_PWDN
## 44     -
##
## 43      CSI2_RST
## 38      CSI1_RST
## 34      CSI0_RST
## 31      CSI3_RST
## 42      CSI2_TRIG
## 36      CSI1_TRIG
## 32      CSI0_TRIG
## 28      CSI3_TRIG
##
## 27      CSI4_RST
## 25      CSI5_RST
## 21      AUX3
## 19      AUX1
## 26      CSI4_TRIG
## 23      CSI5_TRIG
## 20      AUX2
## 18      AUX0

class TriggerPlatform(LatticeICE40Platform):
    device      = "iCE40UP5K"
    package     = "SG48"
    default_clk = "clk12"

    resources   = [
        Resource("clk12", 0, Pins("35", dir="i"),
                 Clock(12e6), Attrs(GLOBAL=True, IO_STANDARD="SB_LVCMOS33")),

        Resource("led0", 0, PinsN("37", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("led1", 0, PinsN("11", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),

        Resource("i2c", 0,
            Subsignal("scl", Pins("4", dir="io")),
            Subsignal("sda", Pins("3", dir="io")),
            Attrs(IO_STANDARD="SB_LVCMOS")
        ),

        Resource("aux", 0, Pins("18", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("aux", 1, Pins("19", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("aux", 2, Pins("20", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("aux", 3, Pins("21", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),

        Resource("csi_rst", 0, Pins("34", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_rst", 1, Pins("38", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_rst", 2, Pins("43", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_rst", 3, Pins("31", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_rst", 4, Pins("27", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_rst", 5, Pins("25", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),

        Resource("csi_trig", 0, Pins("32", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_trig", 1, Pins("36", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_trig", 2, Pins("42", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_trig", 3, Pins("28", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_trig", 4, Pins("26", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),
        Resource("csi_trig", 5, Pins("23", dir="o"), Attrs(IO_STANDARD="SB_LVCMOS33")),

        *SPIFlashResources(0,
            cs_n="16", clk="15", copi="14", cipo="17", attrs=Attrs(IO_STANDARD="SB_LVCMOS33")
        ),
    ]

    connectors = []

    def toolchain_program(self, products, name):
        iceprog = os.environ.get("ICEPROG", "iceprog")
        with products.extract("{}.bin".format(name)) as bitstream_filename:
            subprocess.check_call([iceprog, bitstream_filename])