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

Visual6502.org simulation of an Atari 2600
https://github.com/gregjames/Sim2600.git
Version 0.1, 10/9/2014
Based on work by Greg James, Barry Silverman, Brian Silverman, Ed Spittles,
Michael Steil and others.

** Be patient when running the simulator **

It's not an emulator.  It's a transistor-level simulation
of the actual parts within the 6502 (6507) and TIA chips, 
so it can take several milliseconds to produce a color
for each successive pixel.  The first visible pixels often
don't appear until the 6502 has run for 10,000 half-clock
cycles, after a program has cleared the stack RAM and sent
a few VSYNCs.  It can take about 40,000 TIA half-clock 
cycles to get to that point.

This approach is slow, but it provides a cycle-accurate
picture of exactly what the chips are doing, including
all of the 6502's 'undocumented instructions.'  See the
visual6502.org wiki for more information about those.

Our data for the 6502 and simulation has been adapted to
an FPGA and plugged into original sockets on the Atari
console and Commodore computers.  It runs great, so we're
confident that we've captured an accurate model of the 
chip.  Again, see the wiki and Peter Monta's work.

=== Requirements (ubuntu linux) ===
See install_deps.sh

=== Notes ===
'6502' and '6507' are used interchangeably.  The 6507 is a 6502
in a smaller package with fewer address lines and the NMI and
IRQ interrupts tied high.  

We don't handle hybrid ROM + RAM cartridges or bank switching
within > 4kb ROM cartridges, other than the method used by
Asteroids.  Still, Asteroids doesn't produce any visible pixels
because it sits waiting for someone to hit the console Reset switch.
Some future version will have support for joystick and switch 
input as the simulation clock cycles go by.

This version does not include layer images or polygon geometry
for the chip components.  Arrays or lists are used to hold 
transistors and the wires switched in and out of contact by
the transistors.  These are referred to by their index into
the arrays.  String names are provided for some of the wires, 
which include the chip's i/o pads, power connections, internal
registers, etc.  These names are the keys of the 
CircuitSimulatorBase.wireNames dictionary for each chip.

The 6502 Processor status registers are held in wires named 
'P0', 'P1', ... 'P7'.  They can be querried via calls like:
      sim6502.isHighWN('P0')
See params.py has an example of how the status bits C Z I D B V N
are mapped to 'P0' to 'P7'.  They are:
  C : carry              'P0'
  Z : zero               'P1'
  I : interrupt disable  'P2'
  D : decimal mode       'P3'
  B : in break command   'P4'
  V : overflow           'P6'
  N : negative           'P7'
The bits for registers A, X, and Y have similar labels.  These
are, from lsb to msb: 'A0' to 'A7', 'X0' to 'X7', 'Y0' to 'Y7'.
Same for the stack pointer 'S0' to 'S7', the program counter 
low byte 'PCL', program counter high byte 'PCH', data bus 'DB',
address bus 'AB', etc.


=== articles & more info ===
http://visual6502.org
http://visual6502.org/docs/6502_in_action_14_web.pdf
http://www.pagetable.com/?p=410
http://www.wired.com/2009/03/racing-the-beam/
http://6502.org
http://problemkaputt.de/2k6specs.htm
http://www.computerarcheology.com/wiki/wiki/Atari2600/Asteroids/Code
http://archive.archaeology.org/1107/features/mos_technology_6502_computer_chip_cpu.html

=== TODO === 
Support more bank switching techniques
Finish the C++ version
Lots more.  Drop us a line at visual6502 at gm ail * com if you like
this sort of thing or do something fun with this.

