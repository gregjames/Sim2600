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
# nmosFet.py
# NMOS Field-effect transistor
#

class NmosFet:
    GATE_LOW  = 0
    GATE_HIGH = 1 << 0

    def __init__(self, idIndex, side1WireIndex, side2WireIndex, gateWireIndex):
        
        # Wires switched together when this transistor is on
        self.side1WireIndex = side1WireIndex
        self.side2WireIndex = side2WireIndex
        self.gateWireIndex  = gateWireIndex

        self.gateState = NmosFet.GATE_LOW
        self.index = idIndex

    def __repr__(self):
        rstr = 'NFET %d: %d gate %d [%d, %d]'%(self.index, self.state,
               self.gateWireIndex, self.size1WireIndex, self.side2WireIndex)
        return rstr

