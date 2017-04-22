/* Copyright 2014 Brian Swetland <swetland@frotz.net>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/* reusable verilator sim driver
 * - expects the top module to be sim(clk);
 * - provides clk to module
 * - handles vcd tracing if compiled with TRACE
 * - allows tracefilename to be specified via -o
*/

#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>

#include "Vsim.h"
#include "Vsim__Dpi.h"
#include "verilated.h"
#include <verilated_vcd_c.h>

#define MEMTRACE 0

static uint16_t memory[65536];

static uint64_t now = 0;

void dpi_mem_write(int i, int addr, int data)
{
    memory[addr] = data;

#if MEMTRACE
    printf("%lu W %d: addr 0x%04x, data 0x%04x\n", now, i, addr, data);
#endif
}

void dpi_mem_read(int i, int addr, int *data)
{
    *data = memory[addr];

#if MEMTRACE
    printf("%lu R %d: addr 0x%04x, data 0x%04x\n", now, i, addr, *data);
#endif
}

int main(int argc, char **argv) {
    const char *vcdname = "sim_trace.vcd";
    const char *memname = NULL;
    const char *omemname = NULL;

    while (argc > 1) {
        if (!strcmp(argv[1], "-o")) {
#if TRACE
            if (argc < 2) {
                fprintf(stderr,"error: -o requires argument\n");
                return -1;
            }
            vcdname = argv[2];
            argv += 2;
            argc -= 2;
            continue;
#else
            fprintf(stderr,"error: no trace support\n");
            return -1;
#endif
        } else if (!strcmp(argv[1], "-im")) {
            if (argc < 2) {
                fprintf(stderr, "error: -om requires argument\n");
                return -1;
            }
            memname = argv[2];
            argv += 2;
            argc -= 3;
        } else if (!strcmp(argv[1], "-om")) {
            if (argc < 2) {
                fprintf(stderr, "error: -om requires argument\n");
                return -1;
            }
            omemname = argv[2];
            argv += 2;
            argc -= 3;
        } else {
            break;
        }
    }

    if (memname) {
        /* load memory from .hex file */
        FILE *fp = fopen(memname, "r");
        if (!fp) {
            fprintf(stderr, "cannot open '%s' for reading\n", memname);
            return -1;
        }

        char line[256];
        uint16_t addr = 0;
        while (fgets(line, sizeof(line), fp)) {
            uint32_t data;
            int ret = sscanf(line, "%x", &data);
            if (ret != 1)
                break;

            memory[addr] = data & 0xffff;
            addr++;
        }

        fclose(fp);
    }

    Verilated::commandArgs(argc, argv);
    Verilated::debug(0);
    Verilated::randReset(2);

    Vsim *sim = new Vsim;
    sim->rst = 1;
    sim->clk = 0;

#if TRACE
    Verilated::traceEverOn(true);
    VerilatedVcdC* tfp = new VerilatedVcdC;
    sim->trace(tfp, 99);
    tfp->open(vcdname);
#endif

    while (!Verilated::gotFinish()) {
        sim->clk = !sim->clk;
        sim->eval();
        now += 5;

        if (now > 20)
            sim->rst = 0;

#if TRACE
        tfp->dump(now);
#endif

        if (now > 10000000 * 10)
            break;
    }
#if TRACE
    tfp->close();
#endif
    sim->final();
    delete sim;

    if (omemname != NULL) {
        int fd = open(omemname, O_WRONLY | O_CREAT | O_TRUNC, 0640);
        if (fd < 0) {
            fprintf(stderr, "cannot open '%s' for writing\n", omemname);
            return -1;
        }
        write(fd, memory, sizeof(memory));
        close(fd);
    }

    return 0;
}

