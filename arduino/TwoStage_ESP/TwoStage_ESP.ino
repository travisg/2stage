//
// Copyright (c) 2021 Travis Geiselbrecht
//
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file or at
// https://opensource.org/licenses/MIT

// Program to emulate the 16 bit "two stage" computer ISA
// https://github.com/travisg/2stage
//

// Built for NoceMCU 1.0 ESP8266
// https://arduino.esp8266.com/stable/package_esp8266com_index.json

// Uses MD_MAX72xx library
#define USE_LOCAL_FONT 0
#include <MD_MAX72xx.h>

// Turn on debug statements to the serial output
#define DEBUG  1

#if  DEBUG
#define PRINT(s, x) { Serial.print(F(s)); Serial.print(x); }
#define PRINTS(x) Serial.print(F(x))
#define PRINTD(x) Serial.println(x, DEC)

#else
#define PRINT(s, x)
#define PRINTS(x)
#define PRINTD(x)

#endif

// Define the number of devices we have in the chain and the hardware interface
// NOTE: These pin numbers will probably not work with your hardware and may
// need to be adapted
#define HARDWARE_TYPE MD_MAX72XX::FC16_HW
#define MAX_DEVICES	4

#define CLK_PIN   14  // or SCK  Note: these are the pins for a ESP8266
#define DATA_PIN  13 // or MOSI
#define CS_PIN    15  // or SS

// SPI hardware interface
MD_MAX72XX mx = MD_MAX72XX(HARDWARE_TYPE, CS_PIN, MAX_DEVICES);
// Arbitrary pins
//MD_MAX72XX mx = MD_MAX72XX(HARDWARE_TYPE, DATA_PIN, CLK_PIN, CS_PIN, MAX_DEVICES);

/* Global constants */
#define NUM_REGISTERS  16
#define REGISTER_SIZE 16
#define LR_REGISTER 8
#define SP_REGISTER 9
#define PC_REGISTER 10
#define CR_REGISTER 11

#define CR_V_BIT 0 
#define CR_C_BIT 1 
#define CR_Z_BIT 2 
#define CR_N_BIT 3 
#define CR_BIT_MASK 0xf
#define CR_V_BIT_MASK (1U << CR_V_BIT)
#define CR_C_BIT_MASK (1U << CR_C_BIT)
#define CR_Z_BIT_MASK (1U << CR_Z_BIT)
#define CR_N_BIT_MASK (1U << CR_N_BIT)

/* conditions */
#define COND_EQ       0x0
#define COND_NE       0x1
#define COND_CS       0x2
#define COND_CC       0x3
#define COND_MI       0x4
#define COND_PL       0x5
#define COND_VS       0x6
#define COND_VC       0x7
#define COND_HI       0x8
#define COND_LS       0x9
#define COND_GE       0xa
#define COND_LT       0xb
#define COND_GT       0xc
#define COND_LE       0xd
#define COND_AL       0xe
#define COND_NV       0xf

#define MEMORY_SIZE 0x2000 // Set to 8192 for now,can be expanded to 20 bits

#define INSTRUCTION_INVALID 1 // return code for invalid instruction
#define INSTRUCTION_NOT_IMPLEMENTED 2  // defined but not implemented yet
#define INSTRUCTION_HALT 3 // return code for halt instruction encountered
#define KEYBOARD_INTERRUPT 4  // key was struck while running ***** will need refinement when I/O implemented

/* shift and rotate helpers */
#define LSL(val, shift) \
    (((shift) >= 16) ? 0 : ((val) << (shift)))
#define LSR(val, shift) \
    (((shift) >= 16) ? 0 : ((val) >> (shift)))
#define ASR_SIMPLE(val, shift) \
    (((int16_t)(val)) >> (shift))
#define ASR(val, shift) \
    (((shift) >= 16) ? (BIT(val, 15) ? (int16_t)-1 : 0) : (((int16_t)(val)) >> (shift)))
#define ROR(val, shift) \
    (((val) >> (shift)) | ((val) << (16 - (shift))))

/* bit manipulation macros */
#define BIT(x, bit) ((x) & (1 << (bit)))
#define BIT_SHIFT(x, bit) (((x) >> (bit)) & 1)
#define BITS(x, high, low) ((x) & (((1<<((high)-(low)+1))-1) << (low)))
#define BITS_SHIFT(x, high, low) (((x) >> (low)) & ((1<<((high)-(low)+1))-1))
#define BIT_SET(x, bit) (((x) & (1 << (bit))) ? 1 : 0)

#define ISNEG(x) BIT((x), 15)
#define ISPOS(x) (!(BIT(x, 15)))

#define SIGN_EXTEND(val, topbit) (ASR_SIMPLE(LSL(val, 16-(topbit)), 16-(topbit)))

/*  Global Variables  - For speed */
uint16_t Memory[MEMORY_SIZE];

// Prototype class definitions
class CPU;
class Console;

//********************************************************************
// Class to implement the CPU
//********************************************************************
class CPU
{
  public:
    CPU() = default;  // Constructor

    int Step(); // Step the CPU single instruction step
    int Run(bool slow_display); // Run the CPU
    int Boot(); // Load memory from code here
    uint16_t Get_reg(int register_number); // get value
    void Put_reg(int register_number, uint16_t value); // store value
    void Set_reg_bit(int register_number, int bit, bool val);
    void Show_reg(int register_number);
    void Show_all_registers();

  private:
    int Execute(); // Execute an instruction

    uint16_t do_add(uint16_t a, uint16_t b, int carry_in, bool cr_writeback);
    void set_NZ(uint16_t alu_result);

    uint16_t Regs[NUM_REGISTERS] = {}; 
    uint16_t Regs_displayed[NUM_REGISTERS] {};   // what we last sent to the LED array
    unsigned long last_time = millis();       // time of last clock reading
};  

// CPU method to obtain register value (no value checking, do externally)
inline uint16_t CPU::Get_reg(int register_number) {
  return (Regs[register_number]);
}

// CPU method to store a value in a register (no value checking, do externally)
inline void CPU::Put_reg (int register_number, uint16_t value) {
  // r0 is hard fixed at zero
  if (register_number != 0) {
    Regs [register_number] = value ;
  }
}

inline void CPU::Set_reg_bit(int register_number, int bit, bool val) {
  // r0 is hard fixed at zero
  if (register_number != 0) {
    uint16_t b = (1U << bit);
    // set or clear a single bit in the reg
    Regs [register_number] = (Regs[register_number] & ~b) | (val ? b : 0);
  }
}

// CPU method to output a register contents to the LED panel display
void CPU::Show_reg(int register_number) {

  int beg_row, beg_col;    // beginning row and column
  int16_t value = Regs [register_number];

  // compute the begining row and column number based on the register number
  if (register_number < 8) {
    beg_row = 7 - register_number;
    beg_col = 0;
  } else {
    beg_row = 7 - (register_number-8);
    beg_col = 16;
  }

  // find the xor with previous display to determine which bits have changed
  int xor_mask = value ^ Regs_displayed[register_number];

  // Run a loop outputting each bit in the register
  int mask = 0x8000;
  for (int bit = 0; bit < REGISTER_SIZE; bit++) {
    if ( xor_mask & mask ) {    // skip output if nothing has changed
      mx.setPoint(beg_row,beg_col+bit, (value & mask) != 0);
    }
    mask = mask >> 1;     // move to next bit
  }
  Regs_displayed[register_number] = value;  // remember what we displayed
} // end of Show_register method

// CPU method to output all the registers to the LED display
void CPU::Show_all_registers() {
  for (int i=0; i<NUM_REGISTERS; i++) {
    int16_t value = Regs[i];              // get a value
    if (value != Regs_displayed[i] ) {     // see if it is already been shown
      Show_reg(i);                    // it hasn't, show it
    }
  }
} // end of Show_all_registers method

// CPU method to handle instruction single step
int CPU::Step() {

//  uint16_t address = Regs[PC_REGISTER];
// uint16_t instruction = Memory[address];  // Instruction to be executed
//  Serial.println("CONS> Step -instruction at %04X is %04X \n",address,instruction);

  int ret = Execute(); // just return with execution code
  Show_all_registers();
  return ret;
}

// CPU method to run at full speed
int CPU::Run(bool slow_display) {

  int return_code;

  do {
    // save the current PC before running an instruction
    uint16_t address = Regs[PC_REGISTER];

    // run one cycle of the cpu
    return_code = Execute();

    // piece of code to check the serial port for a break, used in two places below
    auto check_serial = [&return_code]() {
      if (Serial.available()) {      // break on any key for now *********
        __attribute__((unused)) char dummy = Serial.read();  // just dump the interrupt character 
        return_code = KEYBOARD_INTERRUPT;
      }      
    };

    if (slow_display) {
      delay(2);                             // kill a bit of time for the display
      Show_all_registers();                 // output registers to the display
      check_serial();
    } else {
      unsigned long current_time = millis();  // get the time
      if (current_time - last_time > 10) {
        last_time = current_time;
        Show_all_registers();                 // output registers to the display
        check_serial();
      }
    }

    switch (return_code) {
      case INSTRUCTION_HALT: {
        Serial.print("Halt encountered at location 0x");
        Serial.println(address, HEX);
        break;
      }
 
      case INSTRUCTION_INVALID: {
        Serial.print("Invalid instruction at location 0x");
        Serial.print(address, HEX);
        Serial.print(", instruction is 0x");
        Serial.println(Memory[address], HEX);
        break;
      }
 
      case  INSTRUCTION_NOT_IMPLEMENTED: {
        Serial.print("Not implemented instruction 0x");
        Serial.print(address, HEX);
        Serial.print(", instruction is 0x");
        Serial.println(Memory[address], HEX);
        break;
      }
    }
  } while (return_code == 0);

  return 0; // Error noted, return normal to console
}

uint16_t CPU::do_add(uint16_t a, uint16_t b, int carry_in, bool cr_writeback) {
  uint16_t val;

  val = a + b + carry_in;

  if (cr_writeback) {
    bool carry = (ISNEG(a & b) ||                // both operands are negative, or
                 (ISNEG(a ^ b) && ISPOS(val))); // exactly one of the operands is negative, and result is positive
    bool ovl = (!(ISNEG(a ^ b))) && (ISNEG(a ^ val));
    bool neg = ISNEG(val);
    bool zero = val == 0;

    Set_reg_bit(CR_REGISTER, CR_C_BIT, carry);
    Set_reg_bit(CR_REGISTER, CR_V_BIT, ovl);
    Set_reg_bit(CR_REGISTER, CR_N_BIT, neg);
    Set_reg_bit(CR_REGISTER, CR_Z_BIT, zero);
  }
//  CPU_TRACE(10, "do_add: a 0x%x b 0x%x carry_in 0x%x, carry %d, ovl %d\n",
//      a, b, carry_in, *carry, *ovl);

  return val;
}

// set the NZ bits in the condition register
void CPU::set_NZ(uint16_t alu_result) {
  Set_reg_bit(CR_REGISTER, CR_N_BIT, ISNEG(alu_result));
  Set_reg_bit(CR_REGISTER, CR_Z_BIT, alu_result == 0);
}

// given the condition register and a 4 bit condition field, return true or false
static bool test_cond(uint16_t CR, uint16_t cond) {
  bool res = 0;
  switch (cond) {
    case COND_EQ: // Zero set
        if (CR & CR_Z_BIT_MASK)
            res = true;
        break;
    case COND_NE: // Zero clear
        if ((CR & CR_Z_BIT_MASK) == 0)
            res = true;
        break;
    case COND_CS: // Carry set
        if (CR & CR_C_BIT_MASK)
            res = true;
        break;
    case COND_CC: // Carry clear
        if ((CR & CR_C_BIT_MASK) == 0)
            res = true;
        break;
    case COND_MI: // Negative set
        if (CR & CR_N_BIT_MASK)
            res = true;
        break;
    case COND_PL : // Negative clear
        if ((CR & CR_N_BIT_MASK) == 0)
            res = true;
        break;
    case COND_VS: // Overflow set
        if (CR & CR_V_BIT_MASK)
            res = true;
        break;
    case COND_VC: // Overflow clear
        if ((CR & CR_V_BIT_MASK) == 0)
            res = true;
        break;
    case COND_HI: // Carry set and Zero clear
        if ((CR & (CR_C_BIT_MASK|CR_Z_BIT_MASK)) == CR_C_BIT_MASK)
            res = true;
        break;
    case COND_LS: // Carry clear or Zero set
        if (((CR & CR_C_BIT_MASK) == 0) || (CR & CR_Z_BIT_MASK))
            res = true;
        break;
    case COND_GE: { // Negative set and Overflow set, or Negative clear and Overflow clear (N==V)
        auto val = CR & (CR_N_BIT_MASK|CR_V_BIT_MASK);
        if (val == 0 || val == (CR_N_BIT_MASK|CR_V_BIT_MASK))
            res = true;
        break;
    }
    case COND_LT: { // Negative set and Overflow clear, or Negative clear and Overflow set (N!=V)
        auto val = CR & (CR_N_BIT_MASK|CR_V_BIT_MASK);
        if (val == CR_N_BIT_MASK || val == CR_V_BIT_MASK)
            res = true;
        break;
    }
    case COND_GT: { // Zero clear, and either Negative set or Overflow set, or Negative clear and Overflow clear (Z==0 and N==V)
        if ((CR & CR_Z_BIT_MASK) == 0) {
            auto val = CR & (CR_N_BIT_MASK|CR_V_BIT_MASK);
            if (val == 0 || val == (CR_N_BIT_MASK|CR_V_BIT_MASK))
                res = true;
        }
        break;
    }
    case COND_LE: { // Zero set, or Negative set and Overflow clear, or Negative clear and Overflow set (Z==1 or N!=V)
        if (CR & CR_Z_BIT_MASK)
            res = true;

        auto val = CR & (CR_N_BIT_MASK|CR_V_BIT_MASK);
        if (val == CR_N_BIT_MASK || val == CR_V_BIT_MASK)
            res = true;
        break;
    }
    case COND_AL:
    case COND_NV:
        res = true;
        break;
  }
  return res;
}

// CPU method to execute an instruction
int CPU::Execute(){
  // see https://github.com/travisg/2stage/blob/master/isa.txt

  // fetch the next instruction word
  uint16_t instruction = Memory[Regs[PC_REGISTER]];  // Instruction to be executed 
  Regs[PC_REGISTER]++;

  // decode the instruction
  const uint16_t opcode = BITS_SHIFT(instruction, 15, 11); // top 5 bits are the main opcode

  // pre-decode ALU and load/store ops to fetch the d, a, b, and immediates
  int d_reg = 0;
  uint16_t a_val = 0;
  uint16_t b_val = 0;
  if (opcode <= 0b01101) { // low opcodes all have similar bottom layouts
    d_reg = BITS_SHIFT(instruction, 10, 8);
    auto a_reg = BITS_SHIFT(instruction, 7, 5);

    // decode the B register/immediate selector
    if (BIT(instruction, 4) == 0) {
      // 4 bit signed immediate in instructon[3:0]
      b_val = SIGN_EXTEND(BITS(instruction, 4, 0), 4);
    } else if (BITS_SHIFT(instruction, 4, 3) == 0b10) {
      // instruction [2:0] is the b register to select
      b_val = Get_reg(BITS(instruction, 2, 0));
    } else {
      // special selector form
      const bool i = BIT(instruction, 2); // b immediate is in next word
      const bool d = BIT(instruction, 1); // d register is special
      const bool a = BIT(instruction, 0); // a register is special

      // next word contains a 16 bit immediate
      if (i) {
        b_val = Memory[Regs[PC_REGISTER]]; // 16 bit immediate
        Regs[PC_REGISTER]++;
      }

      // D register is actually a special register
      if (d) {
        d_reg += 8; // shift the decoded register into special reg space
      }

      // A register is actually a special register
      if (a) {
        a_reg += 8; // shift the decoded register into special reg space
      }
    }

    // fetch the a value from the register file
    a_val = Get_reg(a_reg);
  }

  // decode ops
  uint16_t temp;
  switch (opcode) {
    case 0b00000: // mov :      d = a + b (no cc writeback)
      Put_reg(d_reg, do_add(a_val, b_val, 0, false));
      break;
    case 0b00001: // add : NZCV d = a + b
      Put_reg(d_reg, do_add(a_val, b_val, 0, true));
      break;
    case 0b00010: // adc : NZCV d = a + b + carry
      Put_reg(d_reg, do_add(a_val, b_val, Get_reg(CR_REGISTER) & CR_C_BIT ? 1 : 0, true));
      break;
    case 0b00011: // sub : NZCV d = a - b
      Put_reg(d_reg, do_add(a_val, ~b_val, 1, true));
      break;
    case 0b00100: // sbc : NZCV d = a - b - borrow
      Put_reg(d_reg, do_add(a_val, ~b_val, Get_reg(CR_REGISTER) & CR_C_BIT ? 1 : 0, true));
      break;
    case 0b00101: // and : NZ   d = a & b
      temp = a_val & b_val;
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;
    case 0b00110: // or  : NZ   d = a | b
      temp = a_val | b_val;
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;
    case 0b00111: // xor : NZ   d = a ^ b
      temp = a_val ^ b_val;
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;
    case 0b01000: // lsl : NZ   d = a << b
      temp = LSL(a_val, b_val);
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;
    case 0b01001: // lsr : NZ   d = a >> b
      temp = LSR(a_val, b_val);
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;
    case 0b01010: // asr : NZ   d = (signed)a >> b
      temp = ASR(a_val, b_val);
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;
    case 0b01011: // ror : NZ   d = rotate(a, b)
      temp = ROR(a_val, b_val);
      set_NZ(temp);
      Put_reg(d_reg, temp);
      break;

    case 0b01100: // ldr : d = memory(a + b)
      temp = a_val + b_val;
      temp = Memory[temp];
      Put_reg(d_reg, temp);
      break;

    case 0b01101: // str : memory(a + b) = d
      temp = a_val + b_val;
      Memory[temp] = Get_reg(d_reg);
      break;

    case 0b01110: // pop  : pop a list of regs from stack, ascending
      return INSTRUCTION_NOT_IMPLEMENTED;
    case 0b01111: // push : push a list of regs on stack, descending
      return INSTRUCTION_NOT_IMPLEMENTED;

    case 0b10000 ... 0b10111: { // branch
      const uint16_t cond = BITS_SHIFT(instruction, 13, 10); // conditional bits to test
      uint16_t target_addr;

      if (cond == COND_NV) { // unconditional branches
        const bool link = BIT(instruction, 9);

        // special case, all 0s in the bottom 4 bits (selecting register 0)
        if (BITS(instruction, 3, 0) == 0) {
          // target is (PC + 1) + immediate in next word
          target_addr = Memory[Regs[PC_REGISTER]++]; // 16 bit immediate
          target_addr += Regs[PC_REGISTER];
        } else {
          // target is held in a register
          auto reg = BITS(instruction, 2, 0);
          // if this bit is set, it's in a special register
          if (BIT(instruction, 3)) {
            reg += 8;
          }

          target_addr = Get_reg(reg);
        }

        // save the current PC in the LR register. PC should be pointing at the next instruction
        if (link) {
          Put_reg(LR_REGISTER, Get_reg(PC_REGISTER));
        }

        Put_reg(PC_REGISTER, target_addr);
      } else { // conditional branches
        uint16_t cond = BITS_SHIFT(instruction, 13, 10);
        //Serial.print("cond 0x"); Serial.print(cond, HEX);
        uint16_t cr = Get_reg(CR_REGISTER) & CR_BIT_MASK;
        //Serial.print(" cr 0x"); Serial.println(cr, HEX);
        if (test_cond(cr, cond)) {
          uint16_t offset = SIGN_EXTEND(BITS(instruction, 9, 0), 9);
          //Serial.print("taking branch, offset 0x"); Serial.println(offset, HEX);
          target_addr = Get_reg(PC_REGISTER) + offset;
          Put_reg(PC_REGISTER, target_addr);
        }
      }

      break;
    }
    case 0b11000 ... 0b11111: // undefined
      return INSTRUCTION_INVALID;
  }

  return 0;
} 

// CPU method for boot, called by console with 'boot' command
int CPU::Boot(void) { // Boot code goes here, called by 'boot' from console
  Serial.println("Boot routine executed") ;

  static const uint16_t test_app[] = {
0x0000, // 0x0000 nop
0x0201, // 0x0001 mov r2, 0x1
0x0b44, // 0x0002 add r3, r2, 0x4
0x1c41, // 0x0003 sub r4, r2, 0x1
0x011e, // 0x0004 mov sp, 0x5
0x0005,
0x001e, // 0x0006 mov lr, 0x6
0x0006,
0x001a, // 0x0008 mov lr, 0x0
0x003b, // 0x0009 mov lr, sp
0x031c, // 0x000a mov r3, 0x99
0x0099,
0x6153, // 0x000c ldr r1, r2, r3
0x6173, // 0x000d ldr r1, r3, r3
0x6993, // 0x000e str r1, r4, r3
0x6a7a, // 0x000f str pc, r3
0x615c, // 0x0010 ldr r1, r2, 0x40
0x0040,
0x611c, // 0x0012 ldr r1, 0x4d2
0x04d2,
0x0201, // 0x0014 mov r2, 0x1
0x605a, // 0x0015 ldr lr, r2
0x615a, // 0x0016 ldr sp, r2
0x635a, // 0x0017 ldr cr, r4
0x021c, // 0x0018 mov r2, here_addr
0x001b,
0x625a, // 0x001a ldr pc, r2
0x001c, // 0x001b .word here
0xbc0a, // 0x001c b pc
0xbe00, // 0x001d bl func
0x0015,
0x0200, // 0x001f mov r2, 0x0
0x0301, // 0x0020 mov r3, 0x1
0x041c, // 0x0021 mov r4, 0x8000
0x8000,
0x051c, // 0x0023 mov r5, 0x8000
0x8000,
0x061c, // 0x0025 mov r6, 0xf000
0xf000,
0xbe00, // 0x0027 bl count_loop_func
0x0007,
0x0a41, // 0x0029 add r2, 0x1
0x4361, // 0x002a lsl r3, 0x1
0x5c81, // 0x002b ror r4, 0x1
0x4da1, // 0x002c lsr r5, 0x1
0x56c1, // 0x002d asr r6, 0x1
0xbc00, // 0x002e b loop
0xfff7,
0x0100, // 0x0030 mov r1, 0x0
0x0921, // 0x0031 add r1, 0x1
0x87fe, // 0x0032 bne count_loop
0xbc08, // 0x0033 b lr
0x0519, // 0x0034 mov r5, lr
0xbc08, // 0x0035 b lr
0x0099, // 0x0036 .word 0099
0x0036, // 0x0037 .word data
0x0074, // 0x0038 .asciiz 'this is a test'
0x0068,
0x0069,
0x0073,
0x0020,
0x0069,
0x0073,
0x0020,
0x0061,
0x0020,
0x0074,
0x0065,
0x0073,
0x0074,
0x0000,
  };

  // load memory with the test app
  for (size_t i = 0; i < sizeof(test_app) / 2; i++) {
    Memory[i] = test_app[i];
  }
  for (auto &r : Regs) {
    r = 0;
  }

  return 0;
}

// ******************************************************************
// Console support routines
// ******************************************************************
#define BUFFER_LENGTH 81
  char inbuf[BUFFER_LENGTH];
  #define MAX_ARGS 10 
#define MAX_ARG_SIZE 80 
  char argv [MAX_ARGS][MAX_ARG_SIZE] ; //parsed command

// Read a line into an input buffer while echoing the characters
void read_line(char inbuf[BUFFER_LENGTH]) {
    char inbyte;
    for (int i = 0; i<BUFFER_LENGTH;i++) inbuf[i]=0;
    bool reading = true;
    int index=0;
    while(reading) {
      if(Serial.available() > 0) {
        inbyte =  Serial.read() ;
        Serial.print(inbyte);

          if ( (inbyte == '\r') ) {
            Serial.print('\n');
            reading = false;
          } 
          else if (inbyte == '\n') {
            reading = false;
          }  
          inbuf[index]=inbyte; index++;
          
       }
    }
}  
  
// getarg function parses buffer into arguments, returning number
// of arguments.

int getarg(char *buffer, char argv[][MAX_ARG_SIZE]) {

  int arg_count = 0 ;
  char* ptr_string ;

  ptr_string = strtok(buffer, " \r\n");
  while (ptr_string != NULL) {


//    Serial.println(" %d %s\n",arg_count,ptr_string);


    strcpy(&argv[arg_count][0],ptr_string) ;
    arg_count++ ;
    ptr_string = strtok (NULL," \r\t\n");
  }
  return arg_count ;
}
/************************************************************
 * Console Class
 * **********************************************************/
class Console
{
  public:
    Console();      // Console constructor
    int Start();    // Console runs until terminated

  private:
    CPU cpu ; // CPU object
    void Print_a_register(int regnum);
    void Print_all_registers(void);
    int Get_register_number();
    void Print_memory_location(unsigned long int  address);
    void convert_hex(int value, int address);

    char *ptr;  // dummy character pointer used by strtol
}; // end of Console class definition

Console::Console() {   //Console constructor
}

// Mainline console method to run the console
int Console::Start(){
  cpu.Boot();       //for default, boot the flashing lights 
  cpu.Run(false);   //and run initially before falling into console

  int num_args ;    // number of arguments on command including command
  bool finish = false;
  do {
    
    cpu.Show_all_registers();
    Serial.println("CONS?> ");
//    fgets( inbuf,81,stdin);
    read_line(inbuf);
    
    num_args = getarg(inbuf, argv) ; // parse line
//    Serial.print("inbuf =");Serial.println(inbuf);
//    Serial.print("num_args = ");Serial.println(num_args);
//    Serial.print("argv[0] =");Serial.println(argv[0]);    

// empty buffer   
    if (num_args == 0 ) {  // buffer was empty, do nothing
    } 
    
// "q" quit command
    else if (strcmp(argv[0],"q") == 0 ) { // quit command
      finish = true;
      break;
    }

// "xr" examine register command
    else if (strcmp(argv[0],"xr") == 0){  //examine register command

      if (num_args > 1 ) { // register number was on command line
        int reg_number ; 
       // sscanf(argv[1],"%x",&reg_number);
       reg_number = strtol(argv[1],&ptr,16);
        Print_a_register(reg_number);

      }

      else {  // none on command line, get it from  user      
        Print_a_register(Get_register_number());
        
      }

    }

// "xra" examine all registers command
    else if (strcmp(argv[0],"xra") == 0){ // examine all registers
      Print_all_registers();
    } 

// "help"  help command
    else if (strcmp(argv[0],"help") == 0){ // print help list
      Serial.println("CONS>List of all commands ");
      Serial.println("help - prints this list ");
      Serial.println("xr - examine register, then prompts for register number in hex ");
      Serial.println("xra - examine all registersxra - prints all register ");
      Serial.println("dr - deposit in register, prompt for register and contents ");
      Serial.println("xm - examine memory, prompt location and number of locs in hex ");
      Serial.println("dm - deposit memory,prompt location terminate input with cntrl  ");
      Serial.println("s - step a single instruction ");
      Serial.println("r or run- run instructions at full speed "); 
      Serial.println("rd - run instructions with delay and display between each ");
      Serial.println("b or boot - boot from internal code routine ");
      Serial.println("q or quit - quit the console ");
      Serial.println("wh - write hex, prompt data and address. Future design will prompt starting and ending address");
    }

// "dr"  deposit in register command
    else if (strcmp(argv[0],"dr") == 0){ // deposit a value in a register

      int reg_number ;
      int16_t value ; // value to enter in register
      
      if (num_args > 1 ) { // register number was on command line
        //sscanf(argv[1],"%x",&reg_number);
        reg_number = strtol(argv[1],&ptr,16);
      }
      else { // register not on command line, get it from user
        reg_number = Get_register_number() ;
      }

      if (num_args > 2) { // value was also on command line
        //sscanf(argv[2],"%x",&value); // decode value
        value = strtol(argv[2],&ptr,16);
        
      }
      else { // value not on command line, get it from user
        
        Serial.println("CONS?>enter value to deposit in hex> ");
     //   fgets( inbuf,81,stdin);
        read_line(inbuf);
        //sscanf(inbuf,"%x",&value);
        value = strtol(inbuf,&ptr,16);
      }
      cpu.Put_reg( reg_number, value );  // store the value 
    }

// "xm" examine memory command
    else if (strcmp(argv[0],"xm") == 0){  // examine memory
      unsigned long int address;
      uint16_t number_words = 0;
      
      if (num_args > 1 ) { // memory address was on command line
       // sscanf(argv[1],"%x",&address);
       address = strtol(argv[1],&ptr,16);
      }     
      
      else { // address not on command line, get it 
        Serial.print("CONS?> enter in hex memory location> ");
        //fgets(inbuf,81,stdin);
        read_line(inbuf);
        //sscanf(inbuf,"%x ",&address) ;
        address = strtol(inbuf,&ptr,16);
        Serial.println("CONS?>enter number of words in hex> ") ;
        //fgets(inbuf,81,stdin);
        read_line(inbuf);
        //sscanf(inbuf,"%x ",&number_words) ;
        number_words = strtol(inbuf,&ptr,16);
        
      }

      if (num_args == 2 ) { // address but no word count was entered
        Serial.println("CONS?>enter number of words in hex> ") ;
        //fgets(inbuf,81,stdin);
        read_line(inbuf);
        //sscanf(inbuf,"%x ",&number_words) ;
        number_words = strtol(inbuf,&ptr,16); 
      }
            
      if (num_args > 2) { // word count was also on the initial command
        //sscanf(argv[2],"%x",&number_words);
        number_words = strtol(argv[2],&ptr,16);
      }
        

      for (int i = 0; i < number_words; i++){ // do the dump
        Print_memory_location(address);
        address++;
      }
    }

// "dm" deposit memory command
    else if (strcmp(argv[0],"dm") == 0) { // deposit memory
      unsigned long int address;
      uint16_t  value;
      char inbuf[21];
      
      if (num_args > 1 ) { // memory address was on command line
        //sscanf(argv[1],"%x",&address);
        address = strtol(argv[1],&ptr,16);
      }     
     
      else { // address not on command line, get it 
          Serial.println("CONS> enter beginning memory address> ") ;
          //fgets(inbuf,21,stdin);
          read_line(inbuf);
          //sscanf(inbuf,"%x ",&address) ;
          address = strtol(inbuf,&ptr,16);
      }
      
      if (num_args > 2) { // a single value was also supplied
        //sscanf(argv[2],"%x",&value) ;
        value = strtol(argv[2],&ptr,16);
        Memory[address] = value;
      }

        else { // need a series of values
      
        Serial.println("CONS> enter consecutive memory values, break with return only ");
        int finished = false;
        do {

           read_line(inbuf);
           num_args = getarg(inbuf, argv) ; // parse line
          
           // Serial.print("num_args ="); Serial.println(num_args);
            if (num_args > 0){
                value = strtol(argv[0],&ptr,16);
                
                Serial.print("Stored ");Serial.print(value,HEX);Serial.print(" in address ");Serial.println(address,HEX);
                Memory[address] = value;
                address++;
             }
             else {
               finished = true;       // terminate on a blank line
             }
        
          } while ( !finished);
        }

    } // end of "dm" hander */
    
// "s" single instruction step command
    else if (strcmp(argv[0],"s") == 0){ // step an instruction
      cpu.Step();
    }
    
// "r" or "run" run at full speed command
    else if ( (strcmp(argv[0],"r") == 0) ||
               (strcmp(argv[0],"run") == 0) ) {
         cpu.Run(false);
    }

// "rd"  run  with display and delay after each instruction
    else if (strcmp(argv[0],"rd")== 0){
      
        cpu.Run(true);
         delay(10);
   
    }    
// "q" or "quit" quit the console
    else if ( (strcmp(argv[0],"q") == 0) ||
               (strcmp(argv[0],"quit") == 0) ) {
        return(0); // return to shell
    }   
// "boot" or "b" execute test code command
    else if((strcmp(argv[0],"boot") == 0) || 
             (strcmp(argv[0],"b") == 0) ){ //execute boot routine
      cpu.Boot();
    }

/*// "write_hex command"
    else if (strcmp(argv[0],"wh") == 0) { //execute test routine
      
      if (num_args > 1){      // There are 2 args
        Serial.println("The Intel HEX format of %d and %d is:",argv[0],argv[1]);
        convert_hex(argv[0],argv[1]);
      }
      else if (num_args < 1 ){  // There are 0 args
        Serial.println("CONS?>enter data to be converted > ");
        //fgets(inbuf,81,stdin);
        real
        sscanf(inbuf,"%x ",&data);
        
        Serial.println("CONS?>enter the address of said data> ");
        fgets(inbuf,81,stdin);
        sscanf(inbuf,"%x ",&ress) ;
        
        Serial.println("The Intel HEX format of %d and %d is:",argv[0],argv[1]);
        convert_hex(argv[0],argv[1]);
      }
      else{           // There are 1 arg
        Serial.println("CONS?>enter data to be converted > ");
        fgets(inbuf,81,stdin);
        sscanf(inbuf,"%x ",&ress);
        
        Serial.println("The Intel HEX format of %d and %d is:",argv[0],argv[1]);
        convert_hex(argv[0],argv[1]);
      } 
    }*/

// Unknown command
    else{
      Serial.println("Command not found \n");
    }

  }while (!finish);
  
  Serial.println("Good day \n");
  return 0; // return success

};

// Console method to print a register
void Console::Print_a_register(int reg_number)
{
  if ( (reg_number >= 0) && (reg_number <NUM_REGISTERS)) {
    Serial.print("CONS> Register ");Serial.print(reg_number,HEX);
    Serial.print("= ");Serial.println(cpu.Get_reg(reg_number),HEX);
  }
  else {
    Serial.println("Illegal register number \n");
  }


  return;
};  
  
// Console method to print all registers
void Console::Print_all_registers(void){

  for ( int i= 0;i<NUM_REGISTERS;i++) {
    Print_a_register(i);
  }
  return;
};
/*// Converting to Intel HEX for writing to files
void Console::convert_hex(int value, int address){
  
  char start_code (':');
  int byte_count = 08;  // It's an 8bit machine, however this may be different
  int record_type = 00; // To be changed
  int data = value;
  int checksum = 00;      // There are functions to calc this, gonna leave it blank for now
  
  
  Serial.println("%c %d %d %d %d %d \n",start_code, byte_count, address, record_type, data, checksum );
  
  
}*/
  

// Console method to prompt for and get register number
int Console::Get_register_number(){
  int regnum ;
  char inbuf[81] ;
  while (true) {
    
    Serial.println("CONS Register Number?> ");
    //fgets(inbuf,81,stdin);
    read_line(inbuf);
    //sscanf(inbuf,"%x",&regnum);
    regnum = strtol(inbuf,&ptr,16);
    if ( (regnum >= 0) && (regnum <NUM_REGISTERS)) {
      return regnum;
    }
    else {
      Serial.println("Illegal register number \n");
    }
  }
}

// Console method to print a memory location
void Console::Print_memory_location(unsigned long int address){
  //Serial.println("CONS> %08X %08X \n",address,Memory[address]);
  Serial.print("CONS> ");Serial.print(address,HEX);Serial.print(" ");Serial.println(Memory[address],HEX);
}       

Console cons;  // Create global console object 

void setup()
{
  Serial.begin(115200);
  
  mx.begin();

//    mx.control(MD_MAX72XX::INTENSITY, 1);
}

void loop()
{
  Serial.println ("Welcome to the 2Stage Machine \n");
  cons.Start();
}
