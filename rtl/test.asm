start:
    mov r2, #1
    mov r3, #7234
    add r1, r3, [r2]
    mov [r1], r3
    add [r1], r3, [r2]
    mov [r2], #9876

loop:
    bl func
    b  #0
    bl  #0
    ;b loop
    ;b start
    ;b r1
    ;bl r1


func:
    mov r5, #5
    b lr
