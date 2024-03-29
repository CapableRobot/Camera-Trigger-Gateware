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

from types import MethodType
from tabulate import tabulate

from migen import *

def apply(obj):
    obj.create = MethodType(create, obj)
    obj.display_table = MethodType(display_table, obj)
    obj.display_defines = MethodType(display_defines, obj)
    
    return obj

def _hex(value):
    return "0x" + format(value, '02X')

def create(self, name, length=1, default=0, ro=False, desc='', **kwargs):
    if not hasattr(self, 'registers'):
        self.registers = []

    reg, addr = [], []
    
    if ro:
        if length == 1:
            reg, addr  = self.add_ro(8, reset=default, **kwargs)

        else:
            for idx in range(length):
                value = 0
                if default != 0:
                    value = ord(default[idx])

                r, a = self.add_ro(8, reset=value, **kwargs)
                reg.append(r)
                addr.append(a)

    else:
        if length == 1:
            reg, addr = self.add_rw(8, reset=default, **kwargs)
        else:
            for idx in range(length):
                r, a = self.add_rw(8, reset=default, **kwargs)
                reg.append(r)
                addr.append(a)

    if type(addr) is list:
        baseaddr = addr[0]
    else:
        baseaddr = addr

    if reg is None or len(reg) == 0:
        print("Cannot add a register '{}' at address {} ({}) as one exists".format(name, baseaddr, hex(baseaddr)))
        print()
        self.display_table()
        raise ValueError

    self.registers.append(
        dict(
            name=name, 
            length=length, 
            addr=baseaddr, 
            default=default, 
            ro=ro, 
            desc=desc
        )
    )
    
    return reg, addr

def display_table(self):
    headers = ["name", "addr", "length", "default", "ro"]
    table = []

    for reg in sorted(self.registers, key=lambda e: e['addr']):
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

