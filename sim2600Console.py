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

import os, struct
from array import array
import params
from sim6502 import Sim6502
from simTIA import SimTIA
from emuPIA import EmuPIA

class Sim2600Console:
    def __init__(self, romFilePath):
        self.sim6507 = Sim6502()
        self.simTIA  = SimTIA()
        self.emuPIA  = EmuPIA()

        self.rom = array('B', [0] * 4096)
        self.bankSwitchROMOffset = 0
        self.programLen = 0

        self.loadProgram(romFilePath)
        self.sim6507.resetChip()

        # The 6507's IRQ and NMI are connected to the supply voltage
        # Setting them to 'pulled high' will keep them high.
        self.sim6507.setPulledHigh(self.sim6507.getWireIndex('IRQ'))
        self.sim6507.setPulledHigh(self.sim6507.getWireIndex('NMI'))
        self.sim6507.recalcWireNameList(['IRQ', 'NMI'])

        # TIA CS1 is always high.  !CS2 is always grounded
        self.simTIA.setPulledHigh(self.simTIA.getWireIndex('CS1'))
        self.simTIA.setPulledLow(self.simTIA.getWireIndex('CS2'))
        self.simTIA.recalcWireNameList(['CS1','CS2'])

        # We're running an Atari 2600 program, so set memory locations
        # for the console's switches and joystick state.
        # Console switches:
        #   d3 set to 1 for color (vs B&W), 
        #   d1 select set to 1 for 'switch not pressed'
        #   d0 set to 1 switch 
        self.writeMemory(0x0282, 0x0B, True)

        # No joystick motion
        # joystick trigger buttons read on bit 7 of INPT4 and INPT5 of TIA
        self.writeMemory(0x0280, 0xFF, True)

    # Memory is mapped as follows:
    # 0x00 - 0x2C  write to TIA
    # 0x30 - 0x3D  read from TIA
    # 0x80 - 0xFF  PIA RAM (128 bytes), also mapped to 0x0180 - 0x01FF for the stack
    # 0280 - 0297  PIA i/o ports and timer
    # F000 - FFFF  Cartridge memory, 4kb
    # We handle 2k, 4k, and 8k cartridges, but only handle the bank switching
    # operations used by Asteroids:  write to 0xFFF8 or 0xFFF9
    #
    def readMemory(self, addr):

      if addr > 0x02FF and addr < 0x8000:
          estr = 'ERROR: 6507 ROM reading addr from 0x1000 to 0x1FFF: 0x%X'%addr
          print(estr)
          return 0

      data = 0
      if (addr >= 0x80 and addr <= 0xFF) or (addr >= 0x180 and addr <= 0x1FF):
          data = self.emuPIA.ram[(addr & 0xFF) - 0x80]
      elif addr >= 0x0280 and addr <= 0x0297:
          data = self.emuPIA.iot[addr - 0x0280]
      elif addr >= 0xF000 or \
           (addr >= 0xD000 and addr <= 0xDFFF and self.programLen == 8192):
          data = self.rom[addr - 0xF000 + self.bankSwitchROMOffset]
      elif addr >= 0x30 and addr <= 0x3D:
          # This is a read from the TIA where the value is
          # controlled by the TIA data bus bits 6 and 7 drive-low
          # and drive-high gates: DB6_drvLo, DB6_drvHi, etc.
          # This is handled below, so no need for anything here
          pass
      elif addr <= 0x2C or (addr >= 0x100 and addr <= 0x12C):
          # This happens all the time, usually at startup when
          # setting data at all writeable addresses to 0.
          msg = 'CURIOUS: Attempt to read from TIA write-only address 0x%4.4X'%(addr)
          #print(msg)
      else:
          # This can happen when the 6507 is coming out of RESET.
          # It sets the first byte of the address bus, issues a read,
          # then sets the second byte, and issues another read to get
          # the correct reset vector.
          msg = 'WARNING: Unhandled address in readMemory: 0x%4.4X'%(addr)
          print(msg)

      cpu = self.sim6507
      tia = self.simTIA

      if cpu.isHigh(cpu.padIndSYNC):
          for wireIndex in tia.dataBusDrivers:
              if tia.isHigh(wireIndex):
                  estr = 'ERROR: TIA driving DB when 6502 fetching ' + \
                         'instruction at addr 0x%X'%(addr)
                  print(estr)
      else:
          if tia.isHigh(tia.indDB6_drvLo):
              data = data & (0xFF ^ (1<<6))
          if tia.isHigh(tia.indDB6_drvHi):
              data = data | (1<<6)
          if tia.isHigh(tia.indDB7_drvLo):
              data = data & (0xFF ^ (1<<7))
          if tia.isHigh(tia.indDB7_drvHi):
              data = data | (1<<7)
          
      if addr & 0x200 and addr < 0x2FF:
          print('6507 READ [0x%X]: 0x%X'%(addr, data))

      cpu.setDataBusValue(data)
      cpu.recalcWireList(cpu.dataBusPads)

      return data

    def writeMemory(self, addr, byteValue, setup=False):
      cpu = self.sim6507
      tia = self.simTIA
      pia = self.emuPIA

      if cpu.isLow(cpu.padReset) and not setup:
          print('Skipping 6507 write during reset.  addr: 0x%X'%(addr))
          return
                
      if addr >= 0xF000 and not setup:
        if self.programLen == 8192:
          if addr == 0xFFF9:
            # switch to bank 0 which starts at 0xD000
            self.bankSwitchROMOffset = 0x2000
          elif addr == 0xFFF8:
            self.bankSwitchROMOffset = 0x1000
        else:
          estr = 'ERROR: 6507 writing to ROM space addr ' + \
                 '0x4.4%X data 0x%2.2X  '%(addr, data)
          if addr >= 0xFFF4 and addr <= 0xFFFB:
            estr += 'This is likely a bank switch strobe we have not implemented'
          elif addr >= 0xF000 and addr <= 0xF07F:
            estr += 'This is likely a cartridge RAM write we have not implemented'
          raise RuntimeException(estr)
                    
      # 6502 shouldn't write to where we keep the console switches
      if (addr == 0x282 or addr == 0x280) and not setup:
          estr = 'ERROR: 6507 writing to console or joystick switches ' + \
                 'addr 0x%4.4X  data 0x%2.2X'%(addr,byteValue)
          print(estr)
          return

      if addr < 0x280:
        msg = '6507 WRITE to [0x%4.4X]: 0x%2.2X  at 6507 halfclock %d'% \
              (addr, byteValue, cpu.halfClkCount)
        print(msg)                
      
      if (addr >= 0x80 and addr <= 0xFF) or (addr >= 0x180 and addr <= 0x1FF):
          pia.ram[(addr & 0xFF) - 0x80] = byteValue
      elif addr >= 0x0280 and addr <= 0x0297:
          pia.iot[addr - 0x0280] = byteValue

          period = None
          if addr == 0x294:
              period = 1
          elif addr == 0x295:
              period = 8
          elif addr == 0x296:
              period = 64
          elif addr == 0x297:
              period = 1024

          if period != None:
              pia.timerPeriod = period
              # initial value for timer read from data bus
              pia.timerVal = cpu.getDataBusValue()
              pia.timerClockCount = 0
              pia.timerFinished = False
      #elif addr <= 0x2C:
      #    # Remember what we wrote to the TIA write-only address
      #    # This is only for bookeeping and debugging and is not
      #    # used for simulation.
      #    self.simTIA.lastControlValue[addr] = byteValue


    def loadProgramBytes(self, progByteList, baseAddr, setResetVector):
        pch = baseAddr >> 8
        pcl = baseAddr & 0xFF
        print('loadProgramBytes base addr $%2.2X%2.2X'%(pch,pcl))

        romDuplicate = 1
        programLen = len(progByteList)
        self.programLen = programLen
        if not programLen in [2048, 4096, 8192]:
            estr = 'No support for program byte list of length %d'%(programLen)
            raise RuntimeException(estr)

        if programLen == 2048:
            # Duplicate ROM contents so it fills all of 0xF000 - 0xFFFF
            romDuplicate = 2
        elif programLen == 8192:
            self.bankSwitchROMOffset = 0x1000

        self.rom = array('B', progByteList * romDuplicate)

        if setResetVector == True:
            print("Setting program's reset vector to program's base address")
            self.writeMemory(0xFFFC, pcl, True)
            self.writeMemory(0xFFFD, pch, True)
        else:
            pcl = self.readMemory(0xFFFA)
            pch = self.readMemory(0xFFFB)
            print("NMI vector:     %X %X"%(pch, pcl))          
            pcl = self.readMemory(0xFFFC)
            pch = self.readMemory(0xFFFD)
            print("Reset vector:   %X %X"%(pch, pcl))
            pcl = self.readMemory(0xFFFE)
            pch = self.readMemory(0xFFFF)
            print("IRQ/BRK vector: %X %X"%(pch, pcl))

    def loadProgram(self, programFilePath):

        if not os.path.exists(programFilePath):
            estr = 'ERROR: Could not find program "%s"'%(programFilePath) + \
                   'from current dir %s'%(os.getcwd())
            raise RuntimeError(estr)

        print('Setting 6502 program to ROM image %s'%(programFilePath))
        self.programFilePath = programFilePath

        # load ROM from file
        of = open (programFilePath, 'rb')
        byteStr = of.read()
        of.close()

        program = []
        progHex = ''
        count = 0
        for byte in byteStr:
            intVal = struct.unpack ('1B', byte)[0]
            progHex += '%2.2X '%intVal
            count += 1
            if count == 8:
                progHex += ' '
            elif count == 16:
                progHex += '\n'
                count = 0
            program.append (intVal)

        baseAddr = 0xF000
        if len(byteStr) == 8192:
            print('Loading 8kb ROM starting from 0x%X'%baseAddr)
        elif len(byteStr) == 2048:
            baseAddr = 0xF800
            print('Loading 2kb ROM starting from 0x%X'%baseAddr)

        self.loadProgramBytes(program, baseAddr, False)

    def updateDataBus(self):
      cpu = self.sim6507
      tia = self.simTIA

      # transfer 6507 data bus to TIA
      # TIA DB0-DB5 are pure inputs
      # TIA DB6 and DB7 can be driven high or low by the TIA
      # TIA CS3 or CS0 high inhibits tia from driving db6 and db7

      i = 0
      numPads = len(cpu.dataBusPads)
      while i < numPads:
        dbPadHigh = cpu.isHigh(cpu.dataBusPads[i])
        tia.setPulled(tia.dataBusPads[i], dbPadHigh)
        i += 1
      tia.recalcWireList(tia.dataBusPads)

      hidrv = False
      for wireInd in tia.dataBusDrivers:
          if tia.isHigh(wireInd):
            hidrv = True
            break

      if hidrv:
        # 6502 SYNC is HIGH when its fetching instruction, so make sure
        # our DB is not being written to by the TIA at this time
        if cpu.isHigh(cpu.padIndSYNC):
            estr = 'ERROR: TIA driving DB when 6502 fetching instruction'
            #report.add (estr)
            print(estr)

    def advanceOneHalfClock(self): #D circuitSim6502, circuitSimTIA, emuPIA):
        cpu = self.sim6507
        tia = self.simTIA
        pia = self.emuPIA

        # Set all TIA inputs to be pulled high.  These aren't updated to
        # reflect any joystick or console switch inputs, but they could be.
        # To give the sim those inputs, you could check the sim halfClkCount,
        # and when it hits a certain value or range of values, set whatever
        # ins you like to low or high.
        # Here, we make an arbitrary choice to set the pads to be pulled
        # high for 10 half clocks.  After this, they should remain pulled
        # high, so choosing 10 half clocks or N > 0 half clocks makes no
        # difference.
        if tia.halfClkCount < 10:
          for wireIndex in tia.inputPads:
            tia.setPulledHigh(wireIndex)
          tia.recalcWireList(tia.inputPads)

        tia.setPulledHigh(tia.padIndDEL)
        tia.recalcWire(tia.padIndDEL)
    
        # TIA 6x45 control ROM will change when R/W goes HI to LOW only if
        # the TIA CLK2 is LOW, so update R/W first, then CLK2.
        # R/W is high when 6502 is reading, low when 6502 is writing

        tia.setPulled(tia.padIndRW, cpu.isHigh(cpu.padIndRW))
        tia.recalcWire(tia.padIndRW)

        addr = cpu.getAddressBusValue()

        # Transfer the state of the 6507 simulation's address bus
        # to the corresponding address inputs of the TIA simulation
        for i, tiaWireIndex in enumerate(tia.addressBusPads):
            padValue = cpu.isHigh(cpu.addressBusPads[i])
            if cpu.isHigh(cpu.addressBusPads[i]):
                tia.setHigh(tiaWireIndex)
            else:
                tia.setLow(tiaWireIndex)
        tia.recalcWireList(tia.addressBusPads)

        # 6507 AB7 goes to TIA CS3 and PIA CS1
        # 6507 AB12 goes to TIA CS0 and PIA CS0, but which 6502 AB line is it?
        # 6507 AB12, AB11, AB10 are not connected externally, so 6507 AB12 is
        # 6502 AB15
        #
        # TODO: return changed/unchanged from setHigh, setLow to decide to recalc
        if addr > 0x7F:
            # It's not a TIA address, so set TIA CS3 high
            # Either CS3 high or CS0 high should disable TIA from writing
            tia.setHigh(tia.padIndCS3)
            tia.setHigh(tia.padIndCS0)
        else:
            # It is a TIA addr from 0x00 to 0x7F, so set CS3 and CS0 low
            tia.setLow(tia.padIndCS3)
            tia.setLow(tia.padIndCS0)
        tia.recalcWireList(tia.padIndsCS0CS3)
    
        self.updateDataBus()

        # Advance the TIA 2nd input clock that is controlled
        # by the 6507's clock generator.
        tia.setPulled(tia.padIndCLK2, cpu.isHigh(cpu.padIndCLK1Out))
        tia.recalcWire(tia.padIndCLK2)
    
        #print('TIA sim num wires added to groups %d, num ant %d'%
        #      (tia.numAddWireToGroup, tia.numAddWireTransistor))
        tia.clearSimStats()

        # Advance TIA 'CLK0' by one half clock
        tia.setPulled(tia.padIndCLK0, not tia.isHigh(tia.padIndCLK0))
        tia.recalcWire(tia.padIndCLK0)
        tia.halfClkCount += 1

        # This is a good place to record the TIA and 6507 (6502)
        # state if you want to capture something like a logic
        # analyzer trace.

        # Transfer bits from TIA pads to 6507 pads
        # TIA RDY and 6507 RDY are pulled high through external resistor, so pull
        # the pad low if the TIA RDY_lowCtrl is on.
        cpu.setPulled(cpu.padIndRDY, not tia.isHigh(tia.indRDY_lowCtrl))
        cpu.recalcWire(cpu.padIndRDY)
    
        # TIA sends a clock to the 6507.  Propagate this clock from the
        # TIA simulation to the 6507 simulation.
        clkTo6507IsHigh = tia.isHigh(tia.padIndPH0)
    
        if clkTo6507IsHigh != cpu.isHigh(cpu.padIndCLK0):

            # Emulate the PIA timer
            # Here at Visual6502.org, we're building a gate-level model
            # of the PIA, but it's not ready yet. 
            pia = self.emuPIA

            if clkTo6507IsHigh:
                # When its reached its end, it counts down from 0xFF every clock
                # (every time the input clock is high, it advances)
                if pia.timerFinished:
                    pia.timerValue -= 1
                    if pia.timerValue < 0:
                        # Assume it doesn't wrap around
                        pia.timerValue = 0
                else:
                    pia.timerClockCount += 1
                    if pia.timerClockCount >= pia.timerPeriod:
                        # decrement interval counter
                        pia.timerValue -= 1
                        pia.timerClockCount = 0
                        if pia.timerValue < 0:
                            pia.timerFinished = True
                            pia.timerValue = 0xFF

            # Advance the 6502 simulation 1 half clock cycle
            if clkTo6507IsHigh:
                cpu.setPulledHigh(cpu.padIndCLK0)
            else:
                cpu.setPulledLow(cpu.padIndCLK0)
    
                # Put PIA count value into memory so 6507 can read it
                # like a regular memory read.
                self.writeMemory(0x284, pia.timerValue)
    
            cpu.recalcWire(cpu.padIndCLK0)
            cpu.halfClkCount += 1

            addr = cpu.getAddressBusValue()

            if cpu.isHigh(cpu.padIndCLK0):
                if cpu.isLow(cpu.padIndRW):
                    data = cpu.getDataBusValue()
                    self.writeMemory(addr, data)
            else:
                # 6507's CLK0 is low
                if cpu.isHigh(cpu.padIndRW):
                    self.readMemory(addr)
