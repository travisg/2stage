start:
    mov r2, 0

again:
    mov r1, 0x8000
    mov r3, 0x8000
loop:
    str r2, r1
    add r1, 1
    sub r3, 1
    bne   loop

    add r2, 1
    b     again

die:
    b   die
