#=================================================
# Copyright (c) 2025, Security Pattern
# All rights reserved.
#
#    This file is part of: Side-channel analysis of three designs in Tiny Tapeout board.
#    This file allows to connect and speak with a Tiny Tapeout board.
#
#    SPDX-License-Identifier: MIT 
#=================================================

import serial, time

class TTSerial:

    def __init__(self, port: str):
        self.ser = serial.Serial(port, 115200)

    def set_project(self, project_id: int):
        self.ser.write(b'\x01')
        self.ser.write(bin(project_id)[2:].rjust(9, '0').encode())

    def set_input(self, input):#: list[int]):
        self.ser.write(b'\x02')
        self.ser.write("".join(str(n) for n in input).encode())

    def read_output(self):
        self.ser.write(b'\x03')
        time.sleep(0.1)
        out = self.ser.read(8)
        #out = self.ser.read_all()
        print(out)
        return [ int(n) - 48 for n in out ]

def do_test():
    s = TTSerial('/dev/tty.usbserial-1430')
    s.set_project(91)

    s.set_input([0,0,0,0,0,0,0,0])
    time.sleep(0.5)
    print(s.read_output())

    s.set_input([0,0,0,0,0,0,0,1])
    time.sleep(0.5)
    print(s.read_output())

    s.set_input([0,0,0,0,0,0,1,1])
    time.sleep(0.5)
    print(s.read_output())

    s.set_input([0,0,0,0,0,1,1,1])
    time.sleep(0.5)
    print(s.read_output())

    time.sleep(2)

    s.set_project(103)

    for i in range(10):
        b = [ int(n) for n in ('0' + bin(i)[2:][::-1])
            .ljust(8, '0') ]
        s.set_input(b)
        time.sleep(1)
    s.set_input([0,0,0,0,0,0,0,0])

    print(s.read_output())