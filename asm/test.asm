start:
    ; catch all of the addressing modes
    add r1, r2
    add r1, r2, r3
    add r1
    add r1, #1234
    add r1, #0x1234
    add r1, r2, #1234
    add r0, [r2]
    add [r0], [r2]
    add lr, sp, pc
    add [lr], [sp]
    mov lr, pc
    mov r1
    mov r1, r2
    not r1
    not r1, r2
    tst r3, r2
    tst r3
    b   r1
    bl  r1
    b   #1      ; short branch
    b   #255    ; short branch
    b   #-256    ; short branch
    b   #256    ; long branch
    b   #-257    ; long branch
    bl  #1234  ; long branch
    bl  #1      ; long branch due to 'l' bit
    b   start   ; a label it has seen
    b   end     ; a label is has not seen
    nop

    ; get all the instructions
    add r1, r2
    sub r1, r2
    and r1, r2
    or r1, r2
    xor r1, r2
    lsl r1, r2
    lsr r1, r2
    asr r1, r2
    b   r1
    nop
    mov r1, r2
    neg r1, r2
    not r1, r2
    teq r1, r2
    tst r1, r2
    cmp r1, r2
    cmn r1, r2

    beq #99
    bne #99
    bcs #99
    bhs #99
    bcc #99
    blo #99
    bmi #99
    bpl #99
    bvs #99
    bvc #99
    bhi #99
    bls #99
    bge #99
    blt #99
    bgt #99
    ble #99

    ; test the immediate range
    add r1, #0
    add r1, #1
    add r1, #7
    add r1, #8
    add r1, #9
    add r1, #-1
    add r1, #-7
    add r1, #-8
end:

    ;b   foobar

    ; some directives
.word   #123
.barf
