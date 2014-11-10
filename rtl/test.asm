start:
    mov r2, 1
    add r3, r2, 4
    sub r4, r2, 1 // should set Z condition

    mov sp, 5
    mov lr, 6
    mov lr, 0
    mov lr, sp

    ldr r1, r2, r3
    str r1, r4, r3

    ldr r1, r2, 64
    ldr r1, 1234

    ldr lr, r2
    ldr sp, r2

    b   pc      // should fall through

    bl  func

loop:
    b  loop
    bl  0
    //b loop
    //b start
    //b r1
    //bl r1

func:
    mov r5, lr
    b lr
