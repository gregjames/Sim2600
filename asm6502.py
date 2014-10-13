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
#--------------------------------------------------------------------------------
#
# This is an experimental assembler for 6502 programs and a small set of test
# programs.
# It's not used in the chip simulation.  It was developed in early 2010 to test
# various things with the 6502 netlist captured for the Visual6502 project.
#
# There are much better 6502 assemblers and tools out there.  See Visual6502.org and:
#   http://6502.org
#   http://skilldrick.github.io/easy6502/#first-program
#   http://www.e-tradition.net/bytes/6502/disassembler.html
#

import os, struct

asm = dict()

# BROKEN:  6502 sim no longer holds its own .memory
def loadProgram (sim, progByteList, baseAddr, setResetVector):
    if sim == None:
        print("Can't loadProgram to a sim that's None")
        return
    pch = baseAddr >> 8
    pcl = baseAddr & 0xFF
    print('BASE $%2.2X%2.2X'%(pch,pcl))

    sim.initMemory (baseAddr, progByteList)
    sm = sim.memory
    if setResetVector == True:
        sm[0xFFFC] = pcl
        sm[0xFFFD] = pch
    else:
        print str(sm[0xFFFC])
        print str(sm[0xFFFD])
        print "Program's reset vector: %X %X"%(sm[0xFFFD], sm[0xFFFC])
        
# Addressing modes syntax
#   http://en.wikibooks.org/wiki/6502_Assembly
# '$' indicates HEX value
# Implied - nothing specified     INX
# Immediate '#'                   LDA  #$22
# Absolute: full 16-bit value     LDX  $D010
# Zero page:  only 8-bit value    LDY  $02
# Relative: value added to PC     BFL  $2D          # -128 to 127
# Abs indexed with X              ADC  $C001, X
# Abs indexed with Y              INC  $F001, Y
# Zero page indexed with X        LDA  $01, X
# Zero page indexed with Y        LDA  $01, Y
# Abs indexed indirect            JMP  ($0001, X)   # only supported by JMP, manual lists "JMP ($1234)"
# Indirect                        JMP  ($5000)      # we use the above form
# Zero page indexed indirect X    ASL  ($15, X)     
# Zero page indirect indexed Y    LSR  ($2A), Y       
#
# indexed indirect: ADC, AND, CMP, EOR, LDA, ORA, SBC, STA   pg 89
# Indirect ref is always Page Zero location from which effective addr low and effective addr high are read.
#   JMP can do absolute indirect jumps.
# 

progs = dict()

cleanStart = """; shared starup sequence
    LDX #$FE    ; will transfer to stack register
    TXS         ; X to stack register
    LDA #$00    ; 
    LDY #$00
    STA  $01FF  ; store $00 on stack, later read to set initial processor status
    PLP         ; processor status from $01FF, leaving stack pointer at $FF
    LDX #$00    ; Above sequence is $0D (13) bytes.  Pad out to 16 with NOP
    NOP         ; $0D
    NOP         ; $0E
    NOP         ; $0F.  Start of real program after this sequence is $8010
    """

testProgramStartAddr = "$8010"

progs['cleanStart'] = cleanStart

progs['INX'] = """      # OK
    %s          ; cleanStart fragment 
    INX         ; inc x by 1
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)
    
progs['INY'] = """      # OK
    %s          ; cleanStart fragment 
    INY         ; inc Y by 1
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['DEX'] = """
    %s          ; cleanStart fragment 
    DEX
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['DEY'] = """
    %s          ; cleanStart fragment 
    DEY
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['TXA'] = """      # OK
    %s          ; cleanStart fragment 
    INX
    TXA         ; x to accum
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['TYA'] = """      # OK
    %s          ; cleanStart fragment 
    INY
    TYA
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['TAX'] = """      # OK ALL
    %s          ; cleanStart fragment 
    INY
    TYA
    TAX
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)
    
progs['TAY'] = """      # OK
    %s          ; cleanStart fragment 
    INX
    TXA         ; X to accum
    TAY         ; accum to Y
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['TXS'] = """      # OK
    %s          ; cleanStart fragment 
    INX
    TXS
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['NOP'] = """      # OK
    %s          ; cleanStart fragment 
    INX
    NOP
    INY
    NOP
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDX #'] = """
    %s          ; cleanStart fragment 
    LDX  #$01
    LDX  #$FF
    LDX  #$80
    LDX  #$00
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDX zp'] = """
    %s          ; cleanStart fragment 
    LDX  $00
    LDX  $01
    LDX  $02
    LDX  $03
    LDX  $04
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDX abs'] = """
    %s          ; cleanStart fragment 
    LDX  $0000
    LDX  $0004
    LDX  $FFFC
    LDX  $FFFD
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDY #'] = """
    %s          ; cleanStart fragment 
    LDY  #$01
    LDY  #$FF
    LDY  #$80
    LDY  #$00
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDY zp'] = """
    %s          ; cleanStart fragment 
    LDY  $00
    LDY  $01
    LDY  $02
    LDY  $03
    LDY  $04
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDY abs'] = """
    %s          ; cleanStart fragment 
    LDY  $0000
    LDY  $0004
    LDY  $FFFC
    LDY  $FFFD
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LDA#'] = """
    %s          ; cleanStart fragment 
    LDA  #$01
    LDA  #$02
    LDA  #$FF
    LDA  #$88
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['PHA_PLA'] = """
    %s          ; cleanStart fragment 
    LDX  #$FF   ; $FF will go from X to stack pointer
    TXS         ; set stack ptr to $FF
    LDA  #$01       
    PHA
    LDA  #$02
    PHA
    LDA  #$FF
    PHA
    LDA  #$88
    PLA         ; start reading back, so should get $FF.  First read of $01FC is ignored
    PLA         ; should get $02
    PLA         ; should get $01
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['ROLzp'] = """
    %s          ; cleanStart fragment 
    ROL  $05        ; memory $05 starts as $01
    LDA  $05
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['EORzp'] = """
    %s          ; cleanStart fragment 
    LDA  #$00
    EOR  $04    ; should get $FF
    EOR  $04    ; should get $00
    EOR  $01    ; should get $11
    EOR  $04    ; should get $EE
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['ASLzp'] = """
    %s          ; cleanStart fragment 
    ASL  $01        ; should write $22, $44, $88, $10, etc.
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['LSRzp'] = """
    %s          ; cleanStart fragment 
    LSR  $06    ; write $40, $20, $10, $08, etc.
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['INCzp'] = """
    %s          ; cleanStart fragment 
    INC  $01
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['set_carry_1'] = """
    %s          ; cleanStart fragment 
    CLC \n CLC \n CLC \n CLC \n CLC \n
    SEC \n SEC \n SEC \n SEC \n SEC \n
    CLC \n CLC \n CLC \n CLC \n
    SEC \n SEC \n SEC \n SEC \n
    CLC \n CLC \n CLC \n
    SEC \n SEC \n SEC \n
    CLC \n CLC \n
    SEC \n SEC \n
    CLC \n SEC \n CLC \n SEC \n CLC \n SEC \n 
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['ASLCarry'] = """
    %s          ; cleanStart fragment 
    CLC
    ASL  $01 \n ASL  $01 \n ASL  $01 \n ASL  $01
    ASL  $01 \n ASL  $01 \n ASL  $01 \n ASL  $01
    ASL  $07 \n ASL  $07 \n ASL  $07 \n ASL  $07
    ASL  $07 \n ASL  $07 \n ASL  $07 \n ASL  $07
    ASL  $07 \n ASL  $07 \n ASL  $07 \n ASL  $07
    INC  $01 \n ASL  $01 \n INC  $01
    INC  $07 \n ASL  $07 \n INC  $07
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['ASLCarry2'] = """
    %s          ; cleanStart fragment 
    CLC
    ASL  $01 \n ASL  $01 \n ASL  $01 \n ASL  $01
    ASL  $01 \n ASL  $01 \n ASL  $01
    CLC
    ASL  $01
    ASL  $07 \n ASL  $07 \n ASL  $07 \n ASL  $07
    ASL  $07 \n ASL  $07 \n ASL  $07 \n ASL  $07
    ASL  $07 \n ASL  $07 \n ASL  $07 \n ASL  $07
    INC  $01 \n ASL  $01 \n INC  $01
    INC  $07 \n ASL  $07 \n INC  $07
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['set_decimal_1'] = """
    %s          ; cleanStart fragment 
    CLD \n CLD \n CLD \n
    SED \n SED \n SED \n
    CLD \n CLD \n
    SED \n SED \n    
    CLD \n SED \n CLD \n SED \n CLD \n SED \n
    CLD \n CLD \n CLD \n CLD
    SED \n SED \n SED \n SED
    CLD \n CLD \n CLD \n
    SED \n SED \n SED \n
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['set_interrupt_dis'] = """
    %s          ; cleanStart fragment 
    CLI \n CLI \n CLI \n CLI \n CLI \n
    SEI \n SEI \n SET \n SEI \n SEI \n
    CLI \n CLI \n CLI \n CLI \n
    SEI \n SEI \n SET \n SEI \n
    CLI \n CLI \n CLI \n
    SEI \n SEI \n SET \n
    CLI \n CLI \n
    SEI \n SEI \n
    CLI \n CLI \n
    SEI \n SEI \n
    CLI \n SEI \n CLI \n SEI \n CLI \n SEI \n CLI \n SEI \n
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['zero_flag'] = """  # 0x00 in memory $0008, non-zero in $0001
    %s          ; cleanStart fragment 
    LDX  $08 \n LDX  $08 \n LDX  $08 \n LDX  $08 \n LDX  $08 \n 
    LDX  $01 \n LDX  $01 \n LDX  $01 \n LDX  $01 \n LDX  $01 \n     
    LDX  $08 \n LDX  $08 \n LDX  $08 \n LDX  $08 \n 
    LDX  $01 \n LDX  $01 \n LDX  $01 \n LDX  $01 \n  
    LDX  $08 \n LDX  $08 \n LDX  $08 \n 
    LDX  $01 \n LDX  $01 \n LDX  $01 \n     
    LDX  $08 \n LDX  $08 \n 
    LDX  $01 \n LDX  $01 \n
    LDX  $08 \n LDX  $08 \n 
    LDX  $01 \n LDX  $01 \n
    LDX  $08 \n LDX  $01 \n LDX  $08 \n LDX  $01 \n LDX  $08 \n LDX  $01 \n
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['neg_flagX'] = """
    %s          ; cleanStart fragment 
    LDX  #$01 \n LDX  #$01 \n LDX  #$01 \n LDX  #$01 \n LDX  #$01 \n 
    LDX  #$FF \n LDX  #$FF \n LDX  #$FF \n LDX  #$FF \n LDX  #$FF \n 
    LDX  #$01 \n LDX  #$01 \n LDX  #$01 \n LDX  #$01 \n
    LDX  #$FF \n LDX  #$FF \n LDX  #$FF \n LDX  #$FF \n
    LDX  #$01 \n LDX  #$01 \n LDX  #$01 \n
    LDX  #$FF \n LDX  #$FF \n LDX  #$FF \n
    LDX  #$01 \n LDX  #$01 \n
    LDX  #$FF \n LDX  #$FF \n
    LDX  #$01 \n LDX  #$01 \n
    LDX  #$FF \n LDX  #$FF \n
    LDX  #$01 \n LDX  #$FF \n LDX  #$01 \n LDX  #$FF \n LDX  #$01 \n LDX  #$FF \n
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['neg_flagY'] = """
    %s          ; cleanStart fragment 
    LDY  #$01 \n LDY  #$01 \n LDY  #$01 \n LDY  #$01 \n LDY  #$01 \n 
    LDY  #$80 \n LDY  #$80 \n LDY  #$80 \n LDY  #$80 \n LDY  #$80 \n 
    LDY  #$01 \n LDY  #$01 \n LDY  #$01 \n LDY  #$01 \n
    LDY  #$80 \n LDY  #$80 \n LDY  #$80 \n LDY  #$80 \n
    LDY  #$01 \n LDY  #$01 \n LDY  #$01 \n
    LDY  #$80 \n LDY  #$80 \n LDY  #$80 \n
    LDY  #$01 \n LDY  #$01 \n
    LDY  #$80 \n LDY  #$80 \n
    LDY  #$01 \n LDY  #$01 \n
    LDY  #$80 \n LDY  #$80 \n
    LDY  #$01 \n LDY  #$80 \n LDY  #$01 \n LDY  #$80 \n LDY  #$01 \n LDY  #$80 \n
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['BRK'] = """
    %s          ; cleanStart fragment 
    LDX #$F4
    TXS
    INX
    BRK
    NOP
    INY
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['DECzp'] = """
    %s          ; cleanStart fragment 
    DEC  $04
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['PLP'] = """  ; pull proc status from stack
    %s          ; cleanStart fragment 
    LDX #$00    ;
    TXS
    PLP         ; read $FF from $0101
    LDX #$01
    TXS
    PLP         ; read $7F from $0102
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['PLPn'] = """
    %s          ; cleanStart fragment 
    PLP \n PLP \n PLP \n PLP \n PLP \n PLP \n PLP \n PLP \n
    PLP \n PLP \n PLP \n PLP \n PLP \n PLP \n PLP \n PLP \n
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['where_stack'] = """
    %s          ; cleanStart fragment 
    LDX #$01    ; stack pointer going to be set to $01
    TXS
    PLA         ; stack pointer is $01, but memory will be read from $02
    LDX #$02
    TXS
    PLA         ; memory will be ready from $03
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

# V is overflow into the sign bit (bit 7).  It goes high when bit 7 turns on
progs['ADC_clearCarry'] = """
    %s          ; cleanStart fragment 
    CLV
    CLC         ; must clear carry at first, otherwise could be 1 at start, yielding $41 for first ADC
    LDA #$00
    ADC #$40 \n ADC #$40 \n ADC #$40 \n ADC #$40 \n ADC #$40 \n ADC #$40 \n 
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['CMP_1'] = """
    %s          ; cleanStart fragment 
    LDA #$11
    CMP  $00
    CMP  $01
    CMP  $02
    CMP #$10
    CMP #$11
    CMP #$12
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['BEQ_1'] = """
    %s          ; cleanStart fragment 
    LDA #$11
    LDX #$81
    CMP #$11
    BEQ  $01    ; branch to DEX
    INX
    DEX
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['BEQ_2'] = """
    %s          ; cleanStart fragment 
    LDA #$11
    LDX #$81
    CMP #$12
    BEQ  $01    ; no branch, so INX and DEX
    INX
    DEX
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['ASL_A'] = """
    %s          ; cleanStart fragment 
    LDA #$01
    ASL  A \n ASL  A \n ASL  A \n ASL  A
    ASL  A \n ASL  A \n ASL  A \n ASL  A \n ASL  A
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)

progs['JSR_RTS'] = """
    %s          ; cleanStart fragment 
    LDX #$80    ; 8010
    LDY #$80    ; 8012
    LDA #$01    ; 8014
    INX         ; 8016
    JSR  $801E  ; 8017
    INY         ; 801A
    JMP %s      ; jump to after 'cleanStart'
    ASL  A      ; 801E  ; shift A left
    RTS         """ %(cleanStart, testProgramStartAddr)

progs['STA_zp'] = """
    %s          ; cleanStart fragment 
    LDA #$01
    STA  $01
    LDX  $01
    LDA #$FF
    STA  $02
    LDX  $02
    JMP %s      ; jump to after 'cleanStart' """%(cleanStart, testProgramStartAddr)


# 2600 Program to cycle the background through all colors and luminances
# Doesn't do any vblank, vsync
# Loaded to offset $8000
progs['TIA_TEST_1'] = """
    %s          ; cleanStart fragment
    LDA #$00
    STA  $01    ; VBLANK
    LDA #$02
    STA  $00    ; VSYNC ON
    STA  $00    ; WSYNC.  3 lines of vsync
    STA  $00
    STA  $00
    LDA #$00    ; going to clear VSYNC
    STA  $00
    ; 2 lines of vblank
    STA  $00    ; WSYNC
    STA  $00
    ; Picutre - cycle background color
    ; ADDR = 
    LDX #$00
    INX         ; 0ffset 40 = $28, I think
    STX  $09    ; COLUBK
    STA  $02    ; WSYNC
    JMP  $8028
"""%(cleanStart)

def initAsm():
    global asm

    # 'immediate' keyed by '#'
    # TST:  Indicates testing done
    #       P  - partial.  Operation was correct for a few small values/cases
    #       P+ - Good for all values.  Untested for all addresses
    #       G  - good.  Operation correct for all values
    #       !  - bad.  Failed for some or all values
    # Notes:
    #  All ,X have bit 9 (0x10) true?
    #
                                #                 # BYTES # NZCIDV    CLK TST COMMENT
    asm['ADC'] = {'#'   :0x69,  #                 2       # NZC--V    2   P   # add mem to accum with carry
                  'zp'  :0x65,  #
                  'zpx' :0x75,  #
                  'abs' :0x6D,  #
                  'absx':0x7D,  #
                  'absy':0x79,  #
                  'zpix':0x61,  #                 2
                  'zpiy':0x71}  #                 2
    asm['AND'] = {'#'   :0x29,  #                 2       # NZ----    2       # AND memory with accum -> accum
                  'zp'  :0x25,  #                 2       #           3
                  'zpx' :0x35,  #                 2       #           4
                  'abs' :0x2D,  #                 3       #           4
                  'absx':0x3D,  #                 3       #           4*
                  'absy':0x39,  #                 3       #           4*
                  'zpix':0x21,  #                 2       #           6
                  'zpiy':0x31}  #                 2       #           5
    asm['ASL'] = {'A'   :0x0A,  # ASL  A          1       # NZC---    2   P   # shift left one bit (mem or accum)
                  'zp'  :0x06,  #                 2                   5   P
                  'zpx' :0x16,  #                 2                   6
                  'abs' :0x0E,  #                 3                   6
                  'absx':0x1E}  #                 3                   7
    asm['BCC'] = {'rel' :0x90}  #                 2       # -------   2**     # branch if C=0 
    asm['BCS'] = {'rel' :0xB0}  #                 2       # -------   2**     # branch if C=1       
    asm['BEQ'] = {'rel' :0xF0}  #                 2       # -------   2** P   # branch if Z=1
    asm['BIT'] = {'zp'  :0x24,  #                 2       # 7Z----6   3       # A&M, M7->N, M6->V
                  'abs' :0x2C}  #                 3       #           4
    asm['BMI'] = {'rel' :0x30}  #                 2       # -------   2**     # branch if N=1
    asm['BNE'] = {'rel' :0xD0}  #                 2       # -------   2**     # branch on Z=0 
    asm['BPL'] = {'rel' :0x10}  #                 2       # -------   2**     # branch on pos result (N flag off)
    asm['BRK'] = 0x00           #                 1       # ----I--   7   P   # Forced interrupt PC+2| P|
    asm['BVC'] = {'rel' :0x50}  #                 2       # -------   2**     # branch on V=0 (no overflow) 
    asm['BVS'] = {'rel' :0x70}  #                 2       # -------   2**     # branch on V=1 (overflow)
    asm['CLC'] = 0x18           #                         #   C       2   G   # clear carry flag
    asm['CLD'] = 0xD8           #                         #     D     2   P   # clear decimal mode
    asm['CLI'] = 0x58           #                         #    I      2   P   # clear interrupt disable
    asm['CLV'] = 0xB8           #                         #      V    2       # clear overflow flag
    asm['CMP'] = {'#'   :0xC9,  #                 2       # NZC---    2   P   # compare memory and accum (A-M)
                  'zp'  :0xC5,  #                 2                   3   P   #  Carry flag set if M <= A
                  'zpx' :0xD5,  #                 2                   4
                  'abs' :0xCD,  #                 3                   4
                  'absx':0xDD,  #                 3                   4*
                  'absy':0xD9,  #                 3                   4*
                  'zpix':0xC1,  #                 2                   6
                  'zpiy':0xD1}  #                 2                   5*
    asm['CPX'] = {'#'   :0xE0,  #                 2       # NZC---    2       # compare memory and index X
                  'zp'  :0xE4,  #                 2       #           3
                  'abs' :0xEC}  #                 3       #           4
    asm['CPY'] = {'#'   :0xC0,  #                 2       # NZC---    2       # compare memory and index Y
                  'zp'  :0xC4,  #                 2       #           3
                  'abs' :0xCC}  #                 3       #           4
    asm['DEC'] = {'zp'  :0xC6,  #                 2       # NZ----    5   P   # decrement memory by 1
                  'zpx' :0xD6,  #                 2                   6
                  'abs' :0xCE,  #                 3                   6
                  'absx':0xDE}  #                 3                   7
    asm['DEX'] = 0xCA           #                         # NZ        2   P   # decrement X by 1
    asm['DEY'] = 0x88           #                         # NZ        2   P   # decrement Y by 1
    asm['EOR'] = {'#'   :0x49,  #                         # NZ        2       # exclusive-or mem with accum -> accum
                  'zp'  :0x45,  #                         #               P
                  'zpx' :0x55,  #
                  'abs' :0x4D,  #
                  'absx':0x5D,  #
                  'absy':0x59,  #
                  'zpix':0x41,  # (Indirect, X)   2       #           6
                  'zpiy':0x51}  # (Indirect), Y   2       #           5*      # 1 more clk if page boundary crossed
    asm['INC'] = {'zp'  :0xE6,  #                         # NZ            P   # increment memory by 1
                  'zpx' :0xF6,  #
                  'abs' :0xEE,  #
                  'absx':0xFE}  #
    asm['INX'] = 0xE8           #                         # NZ        3   P   # increment X by 1
    asm['INY'] = 0xC8           #                         # NZ        3   G   # increment Y by 1
    asm['JMP'] = {'abs'  :0x4C, #                         # ------    3   P   # jump to new location
                  'absix':0x6C} # JMP ($1234, X)  3       # ------    5       
    asm['JSR'] = {'abs' :0x20}  # JSR $1234       3       # ------    6   P   # jump absolute, saving return addr 
    asm['LDA'] = {'#'   :0xA9,  # LDA #$1A        2       # NZ        2   P   # load accum with memory
                  'zp'  :0xA5,  # LDA $01         2
                  'zpx' :0xB5,  # LDA $80, X      2
                  'abs' :0xAD,  # LDA $1234       3
                  'absx':0xBD,  # LDA $1234,X     3
                  'absy':0xB9,  # LDA $1234,Y     3
                  'zpix':0xA1,  # LDA ($12,X)     2
                  'zpiy':0xB1}  # LDA ($12),Y     2          
    asm['LDX'] = {'#'   :0xA2,  #                         # NZ        2   P   # load X with memory
                  'zp'  :0xA6,  #                         #           3   P
                  'zpy' :0xB6,  #                         #           4
                  'abs' :0xAE,  #                         #           4   P
                  'absy':0xBE}  #                         #           4*
    asm['LDY'] = {'#'   :0xA0,  #                         # NZ        2   P   # load Y with memory
                  'zp'  :0xA4,  #                         #           3   P
                  'zpx' :0xB4,  #                         #           4
                  'abs' :0xAC,  #                         #           4   P
                  'absx':0xBC}  #                         #           4*
    asm['LSR'] = {'A'   :0x4A,  #                 1       # _ZC---    2       # shift right one bit (mem or accum)
                  'zp'  :0x46,  #                 2                   5   P
                  'zpx' :0x56,  #                 2                   6
                  'abs' :0x4E,  #                 3                   6
                  'absx':0x5E}  #                 3                   7
    asm['NOP'] = 0xEA           #                         #           2   P   # no operation
    asm['ORA'] = {'#'   :0x09,  #                 2       # NZ----    2       # OR mem with accum -> accum
                  'zp'  :0x05,  #                 2       #           3
                  'zpx' :0x15,  #                 2       #           4
                  'abs' :0x0D,  #                 3       #           4
                  'absx':0x1D,  #                 3       #           4*
                  'absy':0x19,  #                 3       #           4*
                  'zpix':0x01,  #                 2       #           6
                  'zpiy':0x11}  #                 2       #           5
    asm['PHA'] = 0x48           #                         #           3   P   # push accum on stack
    asm['PHP'] = 0x08           #                         #           3       # push processor status on stack
    asm['PLA'] = 0x68           #                         # NZ        4   P   # pull accum from stack
    asm['PLP'] = 0x28           #                         # FromStack 4       # pull processor status from stack
    asm['ROL'] = {'A':   0x2A,  #                 1       # NZC       2       # rotate one bit left (accum or mem)
                  'zp':  0x26,  #                 2                   5   P+
                  'zpx': 0x36,  #                 2                   6
                  'abs': 0x2E,  #                 3                   6
                  'absx':0x3E}  #                 3                   7
    asm['ROR'] = {'A'   :0x6A,  #                 1       # NZC---    2       # rotate one bit right (mem or accum)
                  'zp'  :0x66,  #                 2       #           5
                  'zpx' :0x76,  #                 2       #           6
                  'abs' :0x6E,  #                 3       #           6
                  'absx':0x7E}  #                 3       #           7       
    asm['RTI'] = 0x40           #                 1       # FromStack 6   P   # return from interrupt
    asm['RTS'] = 0x60           #                 1       # ------    6   P   # return from subroutine
    asm['SBC'] = {'#'   :0xE9,  #                 2       # NZC--V    2       # subtract mem from accum with borrow
                  'zp'  :0xE5,  #                 2       #           3
                  'zpx' :0xF5,  #                 2       #           4
                  'abs' :0xED,  #                 3       #           4
                  'absx':0xFD,  #                 3       #           4*
                  'absy':0xF9,  #                 3       #           4*
                  'zpix':0xE1,  #                 2       #           6
                  'zpiy':0xF1}  #                 2       #           5*
    asm['SEC'] = 0x38           #                         #   C       2   G   # set carry flag
    asm['SED'] = 0xF8           #                         #     D     2   P   # set decimal mode
    asm['SEI'] = 0x78           #                         #    I      2   P   # set interrupt disable
    asm['STA'] = {'zp'  :0x85,  #                 2       # ------    3       # store accum in memory
                  'zpx' :0x95,  #                 2       #           4
                  'abs' :0x8D,  #                 3       #           4
                  'absx':0x9D,  #                 3       #           5
                  'absy':0x99,  #                 3       #           5
                  'zpix':0x81,  #                 2       #           6
                  'zpiy':0x91}  #                 2       #           6
    asm['STX'] = {'zp'  :0x86,  #                 2       # ------    3       # store X in memory
                  'zpy' :0x96,  #                 2       #           4
                  'abs' :0x8E}  #                 3       #           4
    asm['STY'] = {'zp'  :0x84,  #                 2       # ------    3       # store Y in memory
                  'zpx' :0x94,  #                 2       #           4
                  'abs' :0x8C}  #                 3       #           4
    asm['TAX'] = 0xAA           #                 1       # NZ----    2   G   # transfer accum to X
    asm['TAY'] = 0xA8           #                 1       # NZ----    2   P   # transfer accum to Y
    asm['TYA'] = 0x98           #                 1       # NZ----    2   G   # transfer Y to accum
    asm['TSX'] = 0xBA           #                 1       # NZ----    2       # transfer stack pointer to X
    asm['TXA'] = 0x8A           #                 1       # NZ----    2   P   # transfer X to accum
    asm['TXS'] = 0x9A           #                 1       # ------    2   P   # transfer X to stack pointer

def assemble (strProg):
    ##logInfo ('programStr', strProg)
    toks = strProg.split ('\n')
    for i, t in enumerate(toks):
        pos = t.find (';')
        if pos > -1:
            t = t[:pos]
        t = t.strip()
        toks[i] = t
    print toks
    prog = []
    compileSteps = []
    for i, t in enumerate(toks):
        i = i + 1        # first line is 1, not 0
        spl = t.split()
        if len(spl) == 0:
            continue
        op = spl[0]
        lineAsm = []
        #print "Assembling line %4.4d, op '%s': %s"%(i, op, t)
        if not asm.has_key(op):
            print 'ERROR: unknown opcode [%s] (line %d): %s'%(op, i, t)
            continue
        else: 
            posD = t.find ('$')
            posComma = t.find (',')
            valMode = 'zp'
            dataBytes = []
            if posD > -1:
                # value between $ and , or end of line
                endValPos = None
                if posComma > -1:
                    endValPos = posComma
                hexVal = t[posD+1 : endValPos]
                hexVal = hexVal.strip()
                lh = len(hexVal)
                #print 'HEX: %s'%hexVal
                if lh == 2:
                    dataBytes = [int(hexVal,16)]
                    # Relative vs. Zero-page will be decided below
                elif lh == 4:
                    valMode = 'abs'
                    # least significant byte before most significant
                    dataBytes = [int(hexVal[2:], 16), int(hexVal[:2], 16)]
                else:
                    print 'ERROR: Hex value [%s] length must be 2 or 4 (line %d): %s'%(hexVal, i, t)

            if type(asm[op]) != type(dict()):
                assert type(asm[op]) == type(1)
                lineAsm = [asm[op]]
            else:
                # parse rest of instruction line looking for () , X Y
                posOpen = t.find ('(')
                posClose = t.find (')')
                posX = t[3:].find ('X')
                posY = t[3:].find ('Y')
                posP = t.find ('#')
                posA = t[3:].find ('A')
                if posP > -1:
                    assert posA == -1, "(line %d): %s"%(i,t)
                    valMode = '#'
                if posA > -1:
                    assert posP == -1, "(line %d): %s"%(i,t)
                    assert posClose == -1, "(line %d): %s"%(i,t)
                    assert posOpen == -1, "(line %d): %s"%(i,t)
                    assert posX == -1, "(line %d): %s"%(i,t)
                    assert posY == -1, "(line %d): %s"%(i,t)
                    valMode = 'A'
                    
                # things we shouldn't find
                assert posP <= posD, "Syntax error '#' must come before '$' (line %d): %s"%(i,t)
                if posP > -1:
                    assert posX == -1 and posY == -1, "Syntax error '#' cannot have X or Y (line %d): %s"%(i,t)
                    assert posComma == -1, "Syntax error '#' cannot have ',' (line %d): %s"%(i,t)
                assert posOpen <= posClose, "Syntax error ')' before '(' (line %d): %s"%(i,t)
                assert t.find('x') == -1, "Syntax error 'x' (line %d): %s"%(i,t)
                assert t.find('y') == -1, "Syntax error 'y' (line %d): %s"%(i,t)
                if posY > -1:
                    assert posClose < posY, "Syntax error ,Y (line %d): %s"%(i,t)
                    assert posX == -1, "(line %d): %s"%(i,t)
                if posX > -1:
                    assert posOpen < poxX, "(line %d): %s"%(i,t)
                    if posClose > -1:
                        assert posClose > posX, "(line %d): %s"%(i,t)
                    assert posY == -1, "(line %d): %s"%(i,t)
                assert posD >= posOpen, "Syntax error: '$' before < '(', '$':%d '(':%d (line %d): %s"%(posD,posOpen,i,t)

                if (valMode == 'zp' or valMode == 'abs') and posOpen > -1:
                    valMode += 'i'
                    
                if posX > -1:
                    valMode += 'x'
                if posY > -1:
                    valMode += 'y'

                modes = asm[op].keys()
                if valMode in modes:
                    lineAsm = [asm[op][valMode]]
                else:
                    if valMode == 'zp' and ('rel' in modes):
                        valMode = 'rel'
                        lineAsm = [asm[op]['rel']]
                lineAsm.extend (dataBytes)
        if len(lineAsm) > 0:
            strBytes = '0x%2.2X, '*len(lineAsm)
            strBytes = strBytes[:-2]
            lat = tuple(lineAsm)
            #print 'LINE ASM as tuple: [%s]'%str(lat)
            strAsm = strBytes % lat
            txt = 'Compiled (%4.4d):  %-15.15s    --> [%s]'%(i, t, strAsm)
            print txt
            compileSteps.append (txt)
            prog.extend (lineAsm)

    ##logInfo ('compileSteps', compileSteps)

    if len(prog) > 0:
        strBytes = '0x%2.2X, '*len(prog)
        strBytes = strBytes[:-2]
        lat = tuple(prog)
        strAsm = strBytes % lat
        print 'PROGRAM: [%s]'%strAsm
        ##logInfo ('programByteList', strAsm)

    return prog
     
# BROKEN:  6502 sim no longer holds its own .memory
def setProgram (sim, progName):
    if progs.has_key (progName):
        print 'Setting 6502 memory to test config and program %s'%progName
        program = assemble (progs[progName])
        # Load program into memory starting from $8000
        sim.initMemory(0x8000, program)
        sm = sim.memory
        # Set some inital memory values used by the test cases
        sm[0xFFFA] = 0x00  # vector low address for NMI
        sm[0xFFFB] = 0x00  # vector high address for NMI
        sm[0xFFFE] = 0x27  # vector low address for IRQ and BRK
        sm[0xFFFF] = 0x05  # vector high address for IRQ and BRK
        sm[0xFFFC] = 0x00  # vector low byte for RESET
        sm[0xFFFD] = 0x80  # vector high byte for RESET, addr = $8000
        sm[0x0527] = 0x40  # RTI, so IRQ and BRK return immediately
        #sm[0x0527] = 0x4C  # JMP
        #sm[0x0528] = 0x00  # JMP low addr byte
        #sm[0x0529] = 0x80  # JMP high addr byte
        # Test values on stack
        sm[0x0101] = 0xFF
        sm[0x0102] = 0x7F  # For status register: All but 'N' bit on
        # Values for test programs
        sm[0x0000] = 0x10
        sm[0x0001] = 0x11
        sm[0x0002] = 0x12
        sm[0x0003] = 0x13
        sm[0x0004] = 0xFF
        sm[0x0005] = 0x01
        sm[0x0006] = 0x80
        sm[0x0007] = 0x03
        sm[0x0008] = 0x00
    else:
        print 'Setting 6502 memory to ROM image %s'%progName
        if os.path.exists (progName):
            # load ROM from file
            of = open (progName, 'rb')
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
                if count == 16:
                    progHex += '\n'
                    count = 0
                program.append (intVal)
            baseAddr = 0xF000
            if len(byteStr) == 8192:
                baseAddr = 0xE000
                print 'Loading 8kb ROM starting from 0x%X'%baseAddr
            elif len(byteStr) == 2048:
                baseAddr = 0xF800
                print 'Loading 2kb ROM starting from 0x%X'%baseAddr
            loadProgram (program, baseAddr, False)
            # We're running Atari 2600 program, so set memory locations for console
            # switches and joystick movement
            sm = sim.memory
            sm[0x0282] = 0x0B   # Console switches: d3 1 for color (vs B&W),
                                # d1 select = 1 switch not pressed, d0 = 1 switch not pressed
            sm[0x0280] = 0xFF   # no joystick motion
            # joystick trigger buttons read on bit 7 of INPT4 and INPT5 of TIA            
        else:
            print "ERROR: Unknown program '%s'"%progName
        

def getProcStatusStr():
    p = getP()  # get processor status bits: (N is MSB)  N V _ B D I Z C  (C is LSB)
    flagStr = ''
    if p & 0x80:  flagStr += 'N'   # N
    else:         flagStr += '-' 
    if p & 0x40:  flagStr += 'V'   # V
    else:         flagStr += '-' 

    flagStr += ''  # _
    if p & 0x10:  flagStr += 'B'   # B
    else:         flagStr += '-' 
    if p & 8:  flagStr += 'D'   # D
    else:      flagStr += '-' 
    if p & 4:  flagStr += 'I'   # I
    else:      flagStr += '-' 
    if p & 2:  flagStr += 'Z'   # Z
    else:      flagStr += '-' 
    if p & 1:  flagStr += 'C'   # C
    else:      flagStr += '-'
    return flagStr

def doQuery():
    flagStr = getProcStatusStr()
    
    str1 = 'CLK: %1s SYNC: %1s  A:%02X X:%02X Y:%02X S:%02X  PC:%02X%02X AB:%04X DB:%02X  RW: %1s P: %s' % (
                        getClock(), getSync(), getA(),getX(), getY(), getStack(), getPCH(),
                        getPCL(), getAddress(), getData(), getRW(), flagStr)
    return str1

def doQuery2():
    flagStr = getProcStatusStr()

    #        inst/data       RDY   IRQ                                                        Processor
    #                |   RES  |     |                        Stack    Program   Address   Data   status
    #        clock   | R/W |  | NMI |  A Reg   X Reg  Y Reg    Ptr    counter      pads   pads    flags
    #            |   |  |  |  |  |  |    |        |      |      |        |           |       |     |
    str1 = 'CLK: PADS:%1s %1s%1s%1s%1s%1s%1s A:%02X X:%02X Y:%02X S:%02X  PC:%02X%02X AB:%04X DB:%02X  P:%s' % (
            getClock(), getSync(), getRW(), getRES(), getRDY(), getNMI(), getIRQ(), getA(), getX(), getY(),
            getStack(), getPCH(), getPCL(), getAddress(), getData(), flagStr)
    return str1

def getClock(sim):
    if sim.isHighWN('CLK0'): return '1'  # clock input high
    else:                    return '0'  # clock input low (2nd half of a clock cycle)
    
def getSync(sim):
    if sim.isHighWN('SYNC'): return 'I'  # instruction
    else:                    return 'D'  # data

def getRW(sim):
    if sim.isHighWN('R/W'):  return 'R'  # read
    else:                    return 'W'  # write

def getRDY(sim):
    if sim.isHighWN('RDY'):  return 'G'  # GO!
    else:                    return 'H'  # halt

def getNMI(sim):
    if sim.isHighWN('NMI'):  return '-'  # no NMI
    else:                    return 'N'  # NMI requested, pad low

def getIRQ(sim):
    if sim.isHighWN('IRQ'):  return '-'  # no IRQ interrupt
    else:                    return 'I'  # IRQ interrupt pad pulled low

def getRES(sim):
    if sim.isHighWN('RES'):  return '-'  # not resetting chip
    else:                    return '#'  # reset pulled low to reset chip
    
def getA(sim):
    return sim.getGen('A', 7)

def getX(sim):
    return sim.getGen('X', 7)

def getY(sim):
    return sim.getGen('Y', 7)

def getStack(sim):
    return sim.getGen('S', 7)

def getPCL(sim):
    return sim.getGen('PCL', 7)

def getPCH(sim):
    return sim.getGen('PCH', 7)

def getP(sim):
    return sim.getGen('P', 7)

def getAddress(sim):
    return sim.getGen ('AB', 15)
    
def getData(sim):
    return sim.getGen ('DB', 7)

def setData(sim, data):
    # Set chip data pads to the 'data' value and update the sim
    sim.setGen(data, 'DB', 8)
    sim.recalcWireNameList(['DB0','DB1','DB2','DB3','DB4','DB5','DB6','DB7'])

#----------------------------------------------------------------------------------

initAsm()


