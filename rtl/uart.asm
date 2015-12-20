start:
    mov     r1, 0xd
    bl      outchar
    mov     r1, 0xa
    bl      outchar

    mov     r2, string

loop:
    ldr     r1, r2
    cmp     r1, 0
    beq     start
    add     r2, 1

    bl      outchar
    b       loop

#   args: r1 character
outchar:
    mov     r6, 0xf000
wait_fifo:
    ldr     r5, r6, 3
    and     r5, 0xff
    beq     wait_fifo

    str     r1, r6
    b       lr

string:
.asciiz "hello"
