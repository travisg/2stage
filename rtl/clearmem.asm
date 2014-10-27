start:
    mov r1, 0
    mov r2, 99
    mov r3, 32768
loop:
    mov [r1], r3
    add r1, 1
    sub r3, 1
    bne   loop

die:
    b   die
