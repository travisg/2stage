start:
    nop

// bunch of random instructions to test the decoder and assembler
    mov r2, 1
    add r3, r2, 4
    sub r4, r2, 1 // should set Z condition

    mov sp, 5
    mov lr, 6
    mov lr, 0
    mov lr, sp

    mov r3, 0x99
    ldr r1, r2, r3
    ldr r1, r3, r3
    str r1, r4, r3
    str pc, r3

    ldr r1, r2, 64
    ldr r1, 1234

    mov r2, 1
    ldr lr, r2
    ldr sp, r2
    ldr cr, r2

    // indirect the pc
    mov r2, here_addr
    ldr pc, r2

here_addr:
    .word here

here:
    b   pc // should fall through, equivalent to branching to next instruction

    // branch and link to a function
    bl  func

    // count up loop, using r1 and r2
    mov r2, 0
    mov r3, 1
    mov r4, 0x8000
    mov r5, 0x8000
    mov r6, 0xf000
loop:
    bl count_loop_func

    // bump r2
    add r2, 1

    lsl r3, 1
    ror r4, 1
    lsr r5, 1
    asr r6, 1

    // start over
    b  loop

    // busy count r1 from 0 to 0xffff
count_loop_func:
    mov r1, 0
    // increment r1. when it wraps to 0 the Z bit will be set and bne will fall through
count_loop:
    add r1, 1
    bne count_loop
    b   lr

func:
    mov r5, lr
    b lr

data:
    .word 0x99
data2:
    .word data

text:
    .asciiz "this is a test"
