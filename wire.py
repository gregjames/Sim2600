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
# wire.py
# Wire is a piece of the circuit whose voltage is either high or low.
# It can drive the gates of transistors and it can be connected
# through transistors to other wires.  A wire represents a group
# of physical parts in a chip where the parts might be metal
# interconnects, polysilicon wires, areas of diffusion, vias, i/o
# pads, or the gates of transistors.
# Certain wires have string names to describe their function, like
# 'VCC' to describe the network that supplies positive voltage, 'GND'
# or 'VSS' to describe the network connected to ground, 'CLK0' for 
# the parts that carry the primary clock signal, etc.
#

class Wire:
    PULLED_HIGH    = 1 << 0
    PULLED_LOW     = 1 << 1
    GROUNDED       = 1 << 2
    HIGH           = 1 << 3
    FLOATING_HIGH  = 1 << 4
    FLOATING_LOW   = 1 << 5
    FLOATING       = 1 << 6

    def __init__(self, idIndex, name, controlTransIndices, transGateIndices, pulled):
        self.index = idIndex
        self.name = name

        # Transistors that switch other wires into connection with this wire
        self.ctInds = controlTransIndices

        # Transistors whos gate is driven by this wire
        self.gateInds = transGateIndices

        # pulled reflects whether or not the wire is connected to
        # a pullup or pulldown.
        self.pulled = pulled

        # state reflects the logical state of the wire as the 
        # simulation progresses.
        self.state = pulled

    def __repr__(self):
        rstr = 'Wire %d "%s": %d  ct %s gates %s'%(self.idIndex, self.name,
               self.state, str(self.ctInds), str(self.gateInds))
        return rstr

    def setHigh(self):
        """ Used to pin a pad or external input high """
        self.pulled = Wire.PULLED_HIGH
        self.state  = Wire.PULLED_HIGH

    def setLow(self):
        """ Used to pin a pad or external input low """
        self.pulled = Wire.PULLED_LOW
        self.state  = Wire.PULLED_LOW

    def setPulledHighOrLow(self, boolHigh):
        """ Used to pin a pad or external input high or low """
        if boolHigh == True:
            self.pulled = Wire.PULLED_HIGH
            self.state  = Wire.PULLED_HIGH
        elif boolHigh == False:
            self.pulled = Wire.PULLED_LOW
            self.state  = Wire.PULLED_LOW
        else:
            raise Exception('Arg to setPulledHighOrLow is not True or False')

    def isHigh(self):
        if self.state == Wire.FLOATING_HIGH or \
           self.state == Wire.PULLED_HIGH or \
           self.state == Wire.HIGH:
            return True
        return False
        
    def isLow(self):
        if self.state == Wire.FLOATING_LOW or \
           self.state == Wire.PULLED_LOW or \
           self.state == Wire.GROUNDED:
            return True
        return False
