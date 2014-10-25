start:
    ; catch all of the addressing modes
    add r1, r2
    add r1, r2, r3
    add r1, #1234
    add r1, #0x1234
    add r1, r2, #1234
    add r0, [r2]
    add [r0], [r2]
    add lr, sp, pc
    add [lr], [sp]
    b   r1
    b   #1234

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

    beq r1
    bne r1
    bcs r1
    bhs r1
    bcc r1
    blo r1
    bmi r1
    bpl r1
    bvs r1
    bvc r1
    bhi r1
    bls r1
    bge r1
    blt r1
    bgt r1
    ble r1
