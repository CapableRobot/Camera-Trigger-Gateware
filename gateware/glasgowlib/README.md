# Glasgow Gateware

The files in this directory are from the [gateware](https://github.com/GlasgowEmbedded/glasgow/tree/master/software/glasgow/gateware) of the open-source [Glasgow project](https://github.com/GlasgowEmbedded/glasgow).

They create registers within the FPGA which can be read and/or written to over an I2C bus.

The [registers_patch.py](../registers_patch.py) file extends the Glasgow Register class with additional functionality for:

- Emitting textual representations of register name, address, default values, & permissions.