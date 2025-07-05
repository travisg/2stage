#define CONSTANT 1234
#define BAR 1234

#define AMACRO() \
    nop \
    nop \
    nop

// comments
; bar

start:
    // catch all of the addressing modes
    nop
    mov r1
    mov r1, r2
    mov lr, pc
    add r1, CONSTANT
    add r1, 0x1234
    add r1, r2
    add r1, r2, r3
    add r1, r2, 1234
    add lr, sp, 0
    add lr, sp, 4
    ldr r1, sp, 4
    ldr r1, r2, 0x4
    ldr r1, r2, r3
    str r1, r4
    str r1, r4, 0x8
    b   r1
    bl  r1
    b   1       // short branch
    b   255     // short branch
    b   -256    // short branch
    b   256     // long branch
    b   -257    // long branch
    bl  1234    // long branch
    bl  1       // long branch due to 'l' bit
    b   start   // a label it has seen
    b   end     // a label is has not seen

    // get all the instructions
    nop         // mov r0, r0 == 0
    mov r0      // mov r0, r0
    mov r0, r0
    mov r1, r2
    add r1, r2
    adc r1, r2
    sub r1, r2
    sbc r1, r2
    and r1, r2
    or r1, r2
    xor r1, r2
    lsl r1, r2
    lsr r1, r2
    asr r1, r2
    ldr r1, r2
    str r1, r2

    // push/pop here

    // pseudo instructions
    neg r1, r1  // sub r1, r0, r1
    neg r1      // sub r1, r0, r1
    neg r1, r2  // sub r1, r0, r2
    not r1, r1  // xor r1, r1, #-1
    not r1      // xor r1, r1, #-1
    not r1, r2  // xor r1, r2, #-1
    teq r1, r2  // xor r0, r1, r2
    tst r1, r2  // and r0, r1, r2
    cmp r1, r2  // sub r0, r1, r2
    cmn r1, r2  // add r0, r1, r2

    // load/stores
    ldr r1, r2, r3
    str r1, r2, r3

    // branches
    beq 99
    bne 99
    bcs 99
    bhs 99
    bcc 99
    blo 99
    bmi 99
    bpl 99
    bvs 99
    bvc 99
    bhi 99
    bls 99
    bge 99
    blt 99
    bgt 99
    ble 99

    // test the immediate range
    add r1, -1
    add r1, 0
    add r1, 1
    add r1, 7
    add r1, -7
    add r1, 8   // long immediate
    add r1, -8  // long immediate

    // reference labels
L0:
    add r1, end
    sub r2, r1, L0

end:

    //b   foobar

    // some directives
.word   123
//.barf
