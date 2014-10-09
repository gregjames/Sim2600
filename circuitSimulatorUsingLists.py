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

        self.lastChipGroupState = 0
        self.groupList = []
        self.groupListLastIndex = 0

    def doWireRecalc(self, wireIndex):

        if wireIndex == self.gndWireIndex or wireIndex == self.vccWireIndex:
            return

        self.lastChipGroupState += 1
        self.groupListLastIndex = 0
        self.groupValue = 0

        self.addWireToGroupList(wireIndex)

        newValue = self.wireList[self.groupList[0]].state
        if self.groupValue & Wire.GROUNDED != 0:
            newValue = Wire.GROUNDED
        elif self.groupValue & Wire.HIGH != 0:
            newValue = Wire.HIGH
        elif self.groupValue & Wire.PULLED_LOW:
            newValue = Wire.PULLED_LOW
        elif self.groupValue & Wire.PULLED_HIGH:
            newValue = Wire.PULLED_HIGH
        elif self.groupValue & Wire.FLOATING_LOW != 0 and \
             self.groupValue & Wire.FLOATING_HIGH != 0:
            newValue = self.countWireSizes()
        elif self.groupValue & Wire.FLOATING_LOW != 0:
            newValue = Wire.FLOATING_LOW
        elif self.groupValue & Wire.FLOATING_HIGH != 0:
            newValue = Wire.FLOATING_HIGH
            
        newHigh = newValue == Wire.HIGH or newValue == Wire.PULLED_HIGH or \
                  newValue == Wire.FLOATING_HIGH

        i = 0
        while i < self.groupListLastIndex:
            wireIndex = self.groupList[i]
            i += 1
            if wireIndex == self.gndWireIndex or wireIndex == self.vccWireIndex:
                continue

            simWire = self.wireList[wireIndex]
            simWire.state = newValue

            # Turn on or off the transistor gates controlled by this wire
            if newHigh == True:
                for transIndex in simWire.gateInds:
                    transistor = self.transistorList[transIndex]
                    if transistor.gateState == NmosFet.GATE_LOW:
                        self.turnTransistorOn(transistor)
            elif newHigh == False:
                for transIndex in simWire.gateInds:
                    transistor = self.transistorList[transIndex]
                    if transistor.gateState == NmosFet.GATE_HIGH:
                        self.turnTransistorOff(transistor)
                
    def turnTransistorOn(self, t):
        t.gateState = NmosFet.GATE_HIGH

        wireInd = t.side1WireIndex
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1
            self.lastChipGroupState += 1

        wireInd = t.side2WireIndex
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1
            self.lastChipGroupState += 1

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
            self.lastChipGroupState += 1

        wireInd = c2Wire
        if self.newRecalcArray[wireInd] == 0:
            self.newRecalcArray[wireInd] = 1
            self.newRecalcOrder[self.newLastRecalcOrder] = wireInd
            self.newLastRecalcOrder += 1
            self.lastChipGroupState += 1

    def addWireToGroupList(self, wireIndex):
        # Do nothing if we've already added the wire to the group
        if self.lastWireGroupState[wireIndex] == self.lastChipGroupState:
            return

        self.numAddWireToGroup += 1

        self.groupList[self.groupListLastIndex] = wireIndex
        self.groupListLastIndex += 1
        self.lastWireGroupState[wireIndex] = self.lastChipGroupState

        if wireIndex == self.gndWireIndex:
            self.groupValue |= Wire.GROUNDED
            return
        elif wireIndex == self.vccWireIndex:
            self.groupValue |= Wire.HIGH
            return

        wire = self.wireList[wireIndex]

        # wire.pulled is 0, 1, or 2
        self.groupValue |= wire.pulled

        if wire.state == Wire.FLOATING_LOW:
            self.groupValue |= Wire.FLOATING_LOW
        elif wire.state == Wire.FLOATING_HIGH:
            self.groupValue |= Wire.FLOATING_HIGH

        for transIndex in wire.ctInds:
            # If the transistor at index 't' is on, add the
            # wires of the circuit on the other side of the 
            # transistor, since wireIndex is connected to them.

            other = -1
            trans = self.transistorList[transIndex]
            if trans.gateState == NmosFet.GATE_LOW:
                continue

            if trans.side1WireIndex == wireIndex:
                other = trans.side2WireIndex
            elif trans.side2WireIndex == wireIndex:
                other = trans.side1WireIndex

            # No need to check if 'other' is already in the groupList:
            #  self.groupList[0:self.groupListLastIndex]
            # That's done in the first line of addWireToGroupList()
            self.addWireToGroupList(other)

    def countWireSizes(self):
        countFl = 0
        countFh = 0
        i = 0
        while i < self.groupListLastIndex:
            wire = self.wireList[self.groupList[i]]
            i += 1
            num = len(wire.ctInds) + len(wire.gateInds)
            if wire.state == Wire.FLOATING_LOW:
                countFl += num
            if wire.state == Wire.FLOATING_HIGH:
                countFh += num
        if countFh < countFl:
            return Wire.FLOATING_LOW
        return Wire.FLOATING_HIGH

    def loadCircuit (self, filePathIn = None):
        data = CircuitSimulatorBase.loadCircuit(self, filePathIn)
        self.groupList = [0] * len(self.wireList)
        return data
