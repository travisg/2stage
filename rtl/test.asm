start:
    mov r2, #1
    mov r3, #7234
    add r1, r3, [r2]
    mov [r1], r3
    add [r1], r3, [r2]
    mov [r2], #9876

    b start  ; (address 0)
