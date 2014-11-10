start:
    mov r2, 1
    add r3, r2, 4
    sub r4, r2, 1 // should set Z condition

    mov sp, 5
    mov lr, 6
    mov lr, 0

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
