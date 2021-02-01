from types import MethodType
from tabulate import tabulate

def apply(obj):
    obj.append = MethodType(append, obj)
    obj.display_table = MethodType(display_table, obj)
    obj.display_defines = MethodType(display_defines, obj)
    
    return obj

def _hex(value):
    return "0x" + format(value, '02X')


def elaborate(self, platform):
        m = Module()
        return m

def append(self, m, name, length=1, default=0, ro=False, desc=''):
    if not hasattr(self, 'registers'):
        self.registers = []

    self.registers.append(
        dict(
            name=name, 
            length=length, 
            addr=self.reg_count, 
            default=default, 
            ro=ro, 
            desc=desc
        )
    )

    reg, addr = [], []

    if ro:
        if length == 1:
            reg, addr  = self.add_ro(8)
            m.d.comb += [reg.eq(default)]

        else:
            for idx in range(length):
                r, a = self.add_ro(8)
                reg.append(r)
                addr.append(a)

                if default != 0:
                    m.d.comb += [r.eq(ord(default[idx]))]
    else:
        if length == 1:
            reg, addr = self.add_rw(8)
        else:
            for idx in range(length):
                r, a = self.add_rw(8)
                reg.append(r)
                addr.append(a)
    
    return reg, addr

def display_table(self):
    headers = ["name", "addr", "length", "default", "ro"]
    table = []

    for reg in self.registers:
        reg['addr'] = _hex(reg['addr'])
        row = [reg[key] for key in headers]

        table.append(row)

    print()
    print("Register Listing")
    print()
    print(tabulate(table, headers, tablefmt="simple"))
    print()

def display_defines(self):

    print()
    print("Register Address Listing")
    print()

    for reg in self.registers:
        
        if type(reg['addr']) is int:
            addr = _hex(reg['addr'])
        else:
            addr = reg['addr']

        name = reg['name'].upper().replace(" ","_")

        print("_REG_{} = const({})".format(name.ljust(20), addr))

    print()

