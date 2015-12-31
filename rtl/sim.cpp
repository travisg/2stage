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

/* reusable verilator testbench driver
 * - expects the top module to be testbench(clk);
 * - provides clk to module
 * - handles vcd tracing if compiled with TRACE
 * - allows tracefilename to be specified via -o
*/

#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <getopt.h>

#include "Vsim.h"
#include "Vsim__Dpi.h"
#include "verilated.h"
#include <verilated_vcd_c.h>

static uint16_t memory[65536];
static bool memtrace = false;

static uint64_t now = 0;

void dpi_mem_write(int i, int addr, int data)
{
    memory[addr] = data;

    if (memtrace)
        printf("%lu W %d: addr 0x%04x, data 0x%04x\n", now, i, addr, data);
}

void dpi_mem_read(int i, int addr, int *data)
{
    *data = memory[addr];

    if (memtrace)
        printf("%lu R %d: addr 0x%04x, data 0x%04x\n", now, i, addr, *data);
}

void usage(int argc, char **argv)
{
    fprintf(stderr, "usage: %s [options]\n", argv[0]);
    fprintf(stderr, "options:\n");
    fprintf(stderr, "\t-h,--help: this help\n");
    fprintf(stderr, "\t-c,--cycles <cycles>:   number of cycles to run before stopping\n");
    fprintf(stderr, "\t-i,--input <hex file>:  input memory image\n");
    fprintf(stderr, "\t-o,--output <hex file>: output memory image\n");
    fprintf(stderr, "\t-m,--memtrace:          trace memory accesses\n");
    fprintf(stderr, "\t-n,--notrace:           do not output trace file\n");
    fprintf(stderr, "\t-v,--vcd <file>:        output trace file, default is sim_trace.vcd\n");
    exit(1);
}

int main(int argc, char **argv)
{
    const char *vcdname = "sim_trace.vcd";
    const char *memname = NULL;
    const char *omemname = NULL;
    uint64_t cycles = 0;
    bool trace = true;
    const struct option long_options[] = {
        {"help",   0,  0,  'h'},
        {"cycles",   1,  0,  'c'},
        {"input",   1,  0,  'i'},
        {"output",   1,  0,  'o'},
        {"memtrace",   0,  0,  'm'},
        {"notrace",   0,  0,  'n'},
        {"vcd",   1,  0,  'v'},
    };

    for (;;) {
        int option_index = 0;
        int c;

        c = getopt_long(argc, argv, "hc:i:mno:v:", long_options, &option_index);
        if (c == -1)
            break;

        switch (c) {
            case 'c':
                cycles = atoll(optarg);
                break;
            case 'i':
                memname = optarg;
                break;
            case 'o':
                omemname = optarg;
                break;
            case 'm':
                memtrace = true;
                break;
            case 'n':
                trace = false;
                break;
            case 'v':
                vcdname = optarg;
                break;
            case 'h':
            default:
                usage(argc, argv);
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
    sim->halt = 0;

    VerilatedVcdC* tfp = 0;
    if (trace) {
        Verilated::traceEverOn(true);
        tfp = new VerilatedVcdC;
        sim->trace(tfp, 99);
        tfp->open(vcdname);
    }

    while (!Verilated::gotFinish()) {
        sim->clk = !sim->clk;
        sim->eval();
        now += 5;

        if (now > 20)
            sim->rst = 0;

        if (trace)
            tfp->dump(now);

        if (sim->clk == 0 && cycles > 0) {
            if (--cycles == 0)
                break;
        }
    }
    if (trace)
        tfp->close();

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

