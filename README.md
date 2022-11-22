# Camera Trigger Gateware

### Background

This FPGA Gateware is for for the Capable Robot [Jetson TX2 / AGX Camera Interface](https://capablerobot.com/products/agx-camera-interface/).  This product:

- Exposes 6x MIPI CSI-2 Camera Interfaces (2-lane) on 22-pin, 0.5mm pitch ribbon cable connectors.
- Has an on-board Lattice ICE40UP5K FPGA provides independent or synchronized camera trigger and reset sigals. 
- Exposes an additional 4 GPIO / sync / trigger signals from the FPGA on an Auxiliary Connector (6-pin JST GH).

![](https://capablerobot.imgix.net/images/agx-camera-interface/PCB-top.jpg?fit=fillmax&fill=solid&fill-color=FFFFFF&trim=auto&pad=20&w=800&h=440)

More information on the hardware is on the [Capable Robot website](https://capablerobot.com/products/agx-camera-interface/).

### Usage

Once flashed onto the SPI Flash, the gateware can be controlled via a set of registers via I2C from the host processor.  Currently, the register mapping is:

```
name               addr      length  default    ro
-----------------  ------  --------  ---------  -----
Product ID         0x00           6  CRZDGE     True
Hardware Revision  0x06           1  0          True
Gateware Revision  0x07           1  1          True
Camera Count       0x0A           1  6          True
GPIO Count         0x0B           1  4          True
Trigger Count      0x0C           1  4          True

Clock Divider      0x14           1  10         False
Power Control      0x15           1  1          False

Crossbar A0        0x20           1  64         False
Crossbar A1        0x21           1  64         False
Crossbar A2        0x22           1  64         False
Crossbar A3        0x23           1  64         False
Crossbar A4        0x24           1  64         False
Crossbar A5        0x25           1  64         False
Crossbar A6        0x26           1  64         False
Crossbar A7        0x27           1  64         False
Crossbar B0        0x28           1  64         False
Crossbar B1        0x29           1  64         False
Crossbar B2        0x2A           1  64         False
Crossbar B3        0x2B           1  64         False
Crossbar B4        0x2C           1  64         False
Crossbar B5        0x2D           1  64         False
Crossbar B6        0x2E           1  64         False
Crossbar B7        0x2F           1  64         False

Trigger Enables    0x3C           1  0          False

Trigger0 Mode      0x40           1  0          False
Trigger0 Interval  0x41           1  0          False
Trigger0 Duration  0x42           1  0          False
Trigger0 Phase     0x43           1  0          False
Trigger1 Mode      0x48           1  0          False
Trigger1 Interval  0x49           1  0          False
Trigger1 Duration  0x4A           1  0          False
Trigger1 Phase     0x4B           1  0          False
Trigger2 Mode      0x50           1  0          False
Trigger2 Interval  0x51           1  0          False
Trigger2 Duration  0x52           1  0          False
Trigger2 Phase     0x53           1  0          False
Trigger3 Mode      0x58           1  0          False
Trigger3 Interval  0x59           1  0          False
Trigger3 Duration  0x5A           1  0          False
Trigger3 Phase     0x5B           1  0          False
```

### Toolchain Installation

Install the [open-source FPGA toolchain](https://github.com/YosysHQ/fpga-toolchain).  

Then install [nmigen](https://github.com/migen/migen) and [tabulate](https://github.com/astanin/python-tabulate) via PIP:

```
pip install -r requirements.txt
```

### Building the Gateware

To target the PCB hardware:

```
python3 gateware/target.py ice
```

To emit a VCD from the simulator:

```
python3 gateware/target.py sim
```

The VCD file can be view using a viewer like [GTKWave](http://gtkwave.sourceforge.net) or [WaveTrace](https://www.wavetrace.io).  In this simulation, 2 ms pass before MODE is set to 0x02 (interval trigger) with a trigger duration of 2 ms and interval of 8 ms.  After 20 ms, the trigger duration and interval change to 5 ms and 10 ms.

![VCD Trace](./images/vcd.png)

### License

This project is distributed under the terms Apache 2.0 license.

See [LICENSE](LICENSE) for details.