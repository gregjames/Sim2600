# Copyright (c) 2014 Greg James, Visual6502.org
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#------------------------------------------------------------------------------
#
# emuPIA.py
# Data for emulating the MOS 6532 RIOT (ram, i/o, + timer) aka. Atari PIA
# (peripheral interface adapter).
# This is the chip with a tiny bit of RAM and a configurable timer.
#
# Here at the Visual6502 project, we have a partial model of the physical parts 
# of he PIA, but don't have a full chip netlist yet, so we use a simple emulator
# for the timer and RAM.
#

from array import array

class EmuPIA:
    def __init__(self):
        self.timerPeriod = 0
        self.timerValue = 0
        self.timerClockCount = 0
        self.timerFinished = False

        # 128 bytes of RAM
        self.ram = array('B', [0] * 0x80)

        # I/O and timer registers
        self.iot = array('B', [0] * (0x297 - 0x280 + 1))
