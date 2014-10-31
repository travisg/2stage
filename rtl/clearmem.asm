start:
    mov r2, 0

again:
    mov r1, 0
    mov r3, 32768
loop:
    mov [r1], r2
    add r1, 1
    sub r3, 1
    bne   loop

    add r2, 1
    b     again

die:
    b   die
