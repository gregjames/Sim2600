

#  The path to the ROM file to load:
#  SpaceInvaders starts to render visible pixels when
#  the cpu halfClkCount reaches about 11000
#romFile = 'roms/SpaceInvaders.bin'
#romFile = 'roms/Pitfall.bin'
romFile = 'roms/DonkeyKong.bin'
#  8kb ROM, spins reading 0x282 switches
#romFile = 'roms/Asteroids.bin'
#  2kb ROM
#romFile = 'roms/Adventure.bin'

#romFile = 'roms/SpaceInvaders.bin'

imageOutputDir = 'outFrames'

# Files describing each chip's network of transistors and wires.
# Also contains names for various wires, some of which are the
# chips input and output pads.
# 
chip6502File = 'chips/net_6502.pkl'
chipTIAFile  = 'chips/net_TIA.pkl'
 
# How many simulation clock changes to run between updates
# of the OpenGL rendering.
numTIAHalfClocksPerRender = 128

# If you'd like to provide additional common sense names for
# a chip's wires, data like the following can be provided to
# CircuitSimulatorBase.updateWireNames(arrayOfArrays) which 
# sets entries in the wireNames dictionary like:
#   wireNames['A0'] = 737;  wireNames['A1'] = 1234
#   wireNames['X3'] = 1648
#
# The node numbers are listed in the status pane of the 
# visual6502.org simulation when you left-click the chip
# image to select part of the circuit:
#  http://visual6502.org/JSSim
# The 6502 chip data, node numbers, and names are the same
# here in this 2600 console simulation as they are in the 
# visual6502 online javascript simulation.
#
#                  # A, X, and Y register bits from lsb to msb
mos6502WireInit = [['A', 737, 1234, 978, 162, 727, 858, 1136, 1653],
                   ['X', 1216, 98, 1, 1648, 85, 589, 448, 777],
                   ['Y', 64, 1148, 573, 305, 989, 615, 115, 843],
                   # stack. only low address has to be stored
                   ['S', 1403, 183, 81, 1532, 1702, 1098, 1212, 1435],
                   # Program counter low byte, from lsb to msb
                   ['PCL', 1139, 1022, 655, 1359, 900, 622, 377, 1611],
                   # Program counter high byte, from lsb to msb
                   ['PCH', 1670, 292, 502, 584, 948, 49, 1551, 205],
                   # status register: C,Z,I,D,B,_,V,N  (C is held in LSB)
                   # 6502 programming manual pgmManJan76 pg 24
                   ['P', 687, 1444, 1421, 439, 1119, 0, 77, 1370],
                  ]

scanlineNumPixels = 228  # for hblank and visible image
frameHeightPixels = 262  # 3 lines vsync, 37 lines vblank,
                         # 192 lines of image, 30 lines overscan

# The order in which these are listed matters.  For busses, they should
# be from lsb to msb.
tiaAddressBusPadNames = ['AB0', 'AB1',  'AB2',  'AB3',  'AB4',  'AB5']
cpuAddressBusPadNames = ['AB0', 'AB1',  'AB2',  'AB3',  'AB4',  'AB5',  'AB6',  'AB7',
                         'AB8', 'AB9', 'AB10', 'AB11', 'AB12', 'AB13', 'AB14', 'AB15']
tiaInputPadNames      = ['I0', 'I1', 'I2', 'I3', 'I4', 'I5']
dataBusPadNames       = ['DB0', 'DB1', 'DB2', 'DB3', 'DB4', 'DB5', 'DB6', 'DB7']
tiaDataBusDrivers     = ['DB6_drvLo', 'DB6_drvHi', 'DB7_drvHi', 'DB7_drvHi']

