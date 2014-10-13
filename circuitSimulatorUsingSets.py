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

from circuitSimulatorBase import CircuitSimulatorBase
from nmosFet import NmosFet
from wire import Wire

class CircuitSimulator(CircuitSimulatorBase):
    def __init__(self):
        CircuitSimulatorBase.__init__(self)

    def doWireRecalc(self, wireIndex):
        if wireIndex == self.gndWireIndex or wireIndex == self.vccWireIndex:
            return

        group = set()
        self.addWireToGroup(wireIndex, group)
        
        newValue = self.getWireValue(group)
        newHigh = newValue == Wire.HIGH or newValue == Wire.PULLED_HIGH or \
                  newValue == Wire.FLOATING_HIGH

        for groupWireIndex in group:
            if groupWireIndex == self.gndWireIndex or \
               groupWireIndex == self.vccWireIndex:
                # TODO: remove gnd and vcc from group?
                continue
            simWire = self.wireList[groupWireIndex]
            simWire.state = newValue
            for transIndex in simWire.gateInds:

                t = self.transistorList[transIndex]

                if newHigh == True and t.gateState == NmosFet.GATE_LOW:
                    self.turnTransistorOn(t)
                if newHigh == False and t.gateState == NmosFet.GATE_HIGH:
                    self.turnTransistorOff(t)

    def turnTransistorOn(self, t):
        t.gateState = NmosFet.GATE_HIGH

        wireInd = t.side1WireIndex
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1

        wireInd = t.side2WireIndex
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1

    def turnTransistorOff(self, t):
        t.gateState = NmosFet.GATE_LOW

        c1Wire = t.side1WireIndex
        c2Wire = t.side2WireIndex
        self.floatWire(c1Wire)
        self.floatWire(c2Wire)

        wireInd = c1Wire
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1

        wireInd = c2Wire
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1


    def getWireValue(self, group):
        # TODO PERF: why turn into a list?
        l = list(group)
        sawFl = False
        sawFh = False
        value = self.wireList[l[0]].state

        for wireIndex in group:
            if wireIndex == self.gndWireIndex:
                return Wire.GROUNDED
            if wireIndex == self.vccWireIndex:
                if self.gndWireIndex in group:
                    return Wire.GROUNDED
                else:
                    return Wire.HIGH
            wire = self.wireList[wireIndex]
            if wire.pulled == Wire.PULLED_HIGH:
                value = Wire.PULLED_HIGH
            elif wire.pulled == Wire.PULLED_LOW:
                value = Wire.PULLED_LOW
                
            if wire.state == Wire.FLOATING_LOW:
                sawFl = True
            elif wire.state == Wire.FLOATING_HIGH:
                sawFh = True

        if value == Wire.FLOATING_LOW or value == Wire.FLOATING_HIGH:
            # If two floating regions are connected together,
            # set their voltage based on whichever region has
            # the most components.  The resulting voltage should
            # be determined by the capacitance of each region.
            # Instead, we use the count of the number of components
            # in each region as an estimate of how much charge 
            # each one holds, and set the result hi or low based
            # on which region has the most components.
            if sawFl and sawFh:
                sizes = self.countWireSizes(group)
                if sizes[1] < sizes[0]:
                    value = Wire.FLOATING_LOW
                else:
                    value = Wire.FLOATING_HIGH
        return value

    def addWireToGroup(self, wireIndex, group):
        self.numAddWireToGroup += 1
        group.add(wireIndex)
        wire = self.wireList[wireIndex]
        if wireIndex == self.gndWireIndex or wireIndex == self.vccWireIndex:
            return
        for t in wire.ctInds:
            self.addWireTransistor (wireIndex, t, group)

    def addWireTransistor(self, wireIndex, t, group):
        self.numAddWireTransistor += 1
        other = -1
        trans = self.transistorList[t]
        if trans.gateState == NmosFet.GATE_LOW:
            return
        if trans.side1WireIndex == wireIndex:
            other = trans.side2WireIndex
        if trans.side2WireIndex == wireIndex:
            other = trans.side1WireIndex
        if other == self.vccWireIndex or other == self.gndWireIndex:
            group.add(other)
            return
        if other in group:
            return
        self.addWireToGroup(other, group)


    def countWireSizes(self, group):
        countFl = 0
        countFh = 0
        for i in group:
            wire = self.wireList[i]
            num = len(wire.ctInds) + len(wire.gateInds)
            if wire.state == Wire.FLOATING_LOW:
                countFl += num
            if wire.state == Wire.FLOATING_HIGH:
                countFh += num
        return [countFl, countFh]

