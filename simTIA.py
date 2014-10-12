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

from array import array
import params

# Choose between two flavors of simulation.  One uses sets
# to track the groups of wires switched together by transistors.
# The other uses lists.

from circuitSimulatorUsingLists import CircuitSimulator
#from circuitSimulatorUsingSets import CircuitSimulator


class SimTIA(CircuitSimulator):
    def __init__(self):
        CircuitSimulator.__init__(self)
        self.loadCircuit(params.chipTIAFile)
        self.colLumToRGB8LUT = []

        # For debugging or inspecting, this can be used to hold
        # the last values written to our write-only control addresses.
        self.lastControlValue = array('B', [0] * (0x2C + 1))

        self.initColLumLUT()

        # Temporarily inhibit TIA from driving DB6 and DB7
        self.setHighWN('CS3')
        self.setHighWN('CS0')

        self.clocksForResetLow = 8
        self.recalcAllWires()

        # The pads of each chip in the chip simulations can be
        # accessed by their name, like 'RDY' or 'CLK0', or by
        # their wire index.  Accessing by wire index is faster
        # so we cache indices here for certain named wires.

        self.addressBusPads = []
        for padName in params.tiaAddressBusPadNames:
            wireIndex = self.getWireIndex(padName)
            self.addressBusPads.append(wireIndex)

        self.dataBusPads = []
        for padName in params.dataBusPadNames:
            wireIndex = self.getWireIndex(padName)
            self.dataBusPads.append(wireIndex)

        self.dataBusDrivers = []
        for padName in params.tiaDataBusDrivers:
            wireIndex = self.getWireIndex(padName)
            self.dataBusDrivers.append(wireIndex)

        self.inputPads = []
        for padName in params.tiaInputPadNames:
            wireIndex = self.getWireIndex(padName)
            self.inputPads.append(wireIndex)

        self.indDB6_drvLo   = self.getWireIndex('DB6_drvLo')
        self.indDB6_drvHi   = self.getWireIndex('DB6_drvHi')
        self.indDB7_drvLo   = self.getWireIndex('DB7_drvLo')
        self.indDB7_drvHi   = self.getWireIndex('DB7_drvHi')
        self.padIndCLK0     = self.getWireIndex('CLK0')
        self.padIndCLK2     = self.getWireIndex('CLK2')
        self.padIndPH0      = self.getWireIndex('PH0')
        self.padIndCS0      = self.getWireIndex('CS0')
        self.padIndCS3      = self.getWireIndex('CS3')
        self.padIndsCS0CS3  = [self.padIndCS0, self.padIndCS3]
        self.padIndRW       = self.getWireIndex('R/W')
        self.padIndDEL      = self.getWireIndex('del')

        # The TIA's RDY_low wire is high when it's pulling the
        # 6502's RDY to ground.  RDY_lowCtrl controls RDY_low
        self.indRDY_lowCtrl = self.getWireIndex('RDY_lowCtrl')
        self.vblank         = self.getWireIndex('VBLANK')
        self.vsync          = self.getWireIndex('VSYNC')
        self.wsync          = self.getWireIndex('WSYNC')
        self.rsync          = self.getWireIndex('RSYNC')

        # Wires that govern the output pixel's luminance and color
        self.L0_lowCtrl     = self.getWireIndex('L0_lowCtrl')
        self.L1_lowCtrl     = self.getWireIndex('L1_lowCtrl')
        self.L2_lowCtrl     = self.getWireIndex('L2_lowCtrl')
        self.colcnt_t0      = self.getWireIndex('COLCNT_T0')
        self.colcnt_t1      = self.getWireIndex('COLCNT_T1')
        self.colcnt_t2      = self.getWireIndex('COLCNT_T2')
        self.colcnt_t3      = self.getWireIndex('COLCNT_T3')

    def getTIAStateStr1(self):
        sigs = {'LUM':['L0_lowCtrl', 'L1_lowCtrl', 'L2_lowCtrl'], 
                'COL':['COLCNT_T0','COLCNT_T1','COLCNT_T2','COLCNT_T3']}
        report = ''
        for s in sigs:
            sStr = ''
            for probe in sigs[s]:
                if self.isHighWN(probe):
                    sStr += '1'
                else:
                    sStr += '0'
            report += s + ' ' + sStr + ' '
        return report

    def initColLumLUT(self):
        # Colors from http://en.wikipedia.org/wiki/Television_Interface_Adapter
        col = [[]] * 16
        col[0]  = [(0,0,0),        (236, 236, 236)]
        col[1]  = [(68, 68, 0),    (252, 252, 104)]
        col[2]  = [(112, 40, 0),   (236, 200, 120)]
        col[3]  = [(132, 24, 0),   (252, 188, 148)]
        col[4]  = [(136, 0, 0),    (252, 180, 180)]
        col[5]  = [(120, 0, 92),   (236, 176, 224)]
        col[6]  = [(72, 0, 120),   (212, 176, 252)]
        col[7]  = [(20, 0, 132),   (188, 180, 252)]
        col[8]  = [(0, 0, 136),    (164, 164, 252)]
        col[9]  = [(0, 24, 124),   (164, 200, 252)]
        col[10] = [(0, 44, 92),    (164, 224, 252)]
        col[11] = [(0, 60, 44),    (164, 252, 212)]
        col[12] = [(0, 60, 0),     (184, 252, 184)]
        col[13] = [(20, 56, 0),    (200, 252, 164)]
        col[14] = [(44, 48, 0),    (224, 236, 156)]
        col[15] = [(68, 40, 0),    (252, 224, 140)]

        # Interpolate linearly between the colors above using 3-bit lum
        # Populate the look up table addressed by a 7-bit col-lum value,
        # where color bits are most significant and luminance bits are
        # least significant

        self.colLumToRGB8LUT = [0]*128
        for intKey in xrange(len(col)):
            colPair = col[intKey]
            start = colPair[0]
            end   = colPair[1]
            dif = ()
            for i, startv in enumerate(start):
                # result is tuple of same dim as 'start' and 'end'      
                dif += (end[i] - startv,)
            # lumInt from 0 to 7
            for lumInt in xrange(8):
                lumFrac = lumInt / 7.0
                ctup = ()
                for i, startv in enumerate(start):
                    ctup += (int(startv + dif[i]*lumFrac),)
                colLumInd = (intKey << 3) + lumInt
                self.colLumToRGB8LUT[colLumInd] = ctup

    def get3BitLuminance(self):
        lum = 7

        # If L0_lowCtrl is high, then the pad for the least significant bit of
        # luminance is pulled low, so subtract 1 from the luminance
        if self.isHigh(self.L0_lowCtrl):
            lum -= 1

        # If L1_lowCtrl is high, then the pad for the twos bit of luminance
        # is pulled low, so subtract 2 from the luminance
        if self.isHigh(self.L1_lowCtrl):
            lum -= 2

        # If the most significant bit is pulled low, subtract 4
        if self.isHigh(self.L2_lowCtrl):
            lum -= 4

        return lum

    def get4BitColor(self):
        col = 0
        if self.isHigh(self.colcnt_t0):
            col += 1
        if self.isHigh(self.colcnt_t1):
            col += 2
        if self.isHigh(self.colcnt_t2):
            col += 4
        if self.isHigh(self.colcnt_t3):
            col += 8
        return col

    def getColorRGBA8(self):
        lum = self.get3BitLuminance()
        col = self.get4BitColor()

        # Lowest 4 bits of col, shift them 3 bits to the right,
        # and add the low 3 bits of luminance
        index = ((col & 0xF) << 3) + (lum & 0x7)

        rgb8Tuple = self.colLumToRGB8LUT[index]
        return (rgb8Tuple[0] << 24) | (rgb8Tuple[1] << 16) | \
               (rgb8Tuple[2] << 8) | 0xFF

