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

import params

# Choose between two flavors of simulation.  One uses sets
# to track the groups of wires switched together by transistors.
# The other uses lists.

from circuitSimulatorUsingLists import CircuitSimulator
#from circuitSimulatorUsingSets import CircuitSimulator


class Sim6502(CircuitSimulator):
    def __init__(self):
        CircuitSimulator.__init__(self)

        self.loadCircuit(params.chip6502File)

        # No need to update the names based on params.mos6502WireInit.
        # The names have already been saved in the net_6502.pkl file.
        # This is provided as an example of how to update a chip's 
        # wires with your own string names.
        #self.updateWireNames(params.mos6502WireInit)

        # Store indices into the wireList.  This saves having
        # to look up the wires by their string name from the
        # wireNames dict.
        self.addressBusPads = []
        for padName in params.cpuAddressBusPadNames:
            wireIndex = self.getWireIndex(padName)
            self.addressBusPads.append(wireIndex)

        self.dataBusPads = []
        for padName in params.dataBusPadNames:
            wireIndex = self.getWireIndex(padName)
            self.dataBusPads.append(wireIndex)

        self.padIndRW      = self.getWireIndex('R/W')
        self.padIndCLK0    = self.getWireIndex('CLK0')
        self.padIndRDY     = self.getWireIndex('RDY')
        self.padIndCLK1Out = self.getWireIndex('CLK1OUT')
        self.padIndSYNC    = self.getWireIndex('SYNC')
        self.padReset      = self.getWireIndex('RES')

    def getAddressBusValue(self):
        addr = 0
        shift = 0
        for wireIndex in self.addressBusPads:
            if self.isHigh(wireIndex):
                addr |= (1 << shift)
            shift += 1
        return addr
        
    def getDataBusValue(self):
        data = 0
        shift = 0
        for wireIndex in self.dataBusPads:
            if self.isHigh(wireIndex):
                data |= 1 << shift
            shift += 1
        return data

    def setDataBusValue(self, value):
        shift = 0
        for wireIndex in self.dataBusPads:
            if (value & (1 << shift)) != 0:
                self.setHigh(wireIndex)
            else:
                self.setLow(wireIndex)
            shift += 1

    def getStateStr1(self):
        return str('6502 CLK %d RES %d RDY %d  ADDR 0x%4.4X  DB 0x%2.2X'%
              (self.isHighWN('CLK0'), 
               self.isHighWN('RES'), self.isHighWN('RDY'), 
               self.getAddressBusValue(), self.getDataBusValue()))

    def resetChip(self):
        print('Starting 6502 reset sequence: pulling RES low')
        self.recalcAllWires()
        self.setLowWN('RES')
        self.setHighWN('IRQ')  # no interrupt
        self.setHighWN('NMI')  # no interrupt
        self.setHighWN('RDY')  # let the chip run.  Will connect to TIA with pullup
        self.recalcWireNameList(['IRQ','NMI','RES','RDY'])
        for i in xrange(4):
            if i % 2:
                self.setLowWN('CLK0')
            else:
                self.setHighWN('CLK0')
            self.recalcNamedWire('CLK0')

        print('Setting 6502 RES high')
        self.setHighWN('RES')
        self.recalcNamedWire('RES')

        print('Finished 6502 reset sequence')
