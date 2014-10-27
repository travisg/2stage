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

#include "Vsim.h"
#include "verilated.h"
#include <verilated_vcd_c.h>

static uint16_t imemory[65536];
static uint16_t dmemory[65536];

static uint64_t now = 0;

static void imem_transaction(uint8_t clk, uint8_t re, uint16_t iaddr, uint16_t *idata)
{
    static uint8_t lastclk = 0;
    static uint16_t lastaddr = 0;

    //printf("now %lu clk %d re %d iaddr 0x%x\n", now, clk, re, iaddr);

    if (clk == 1 && clk != lastclk) {
        *idata = imemory[lastaddr];
    }

    lastclk = clk;
    lastaddr = iaddr;
}

static void dmem_transaction(uint8_t clk, uint8_t re, uint16_t raddr, uint16_t *rdata, uint8_t we, uint16_t waddr, uint16_t wdata)
{
    static uint8_t lastclk = 0;
    static uint8_t lastre = 0;
    static uint16_t lastraddr = 0;
    static uint8_t lastwe = 0;
    static uint16_t lastwaddr = 0;
    static uint16_t lastwdata = 0;

    //printf("now %lu clk %d re %d raddr 0x%x we %d waddr 0x%x wdata 0x%x\n",
    //    now, clk, re, raddr, we, waddr, wdata);

    if (clk == 1 && clk != lastclk && lastre) {
        *rdata = dmemory[lastraddr];
    }

    if (clk == 1 && clk != lastclk && lastwe) {
        //printf("writing 0x%x to 0x%x\n", lastwdata, lastwaddr);
        dmemory[lastwaddr] = lastwdata;
    }

    lastclk = clk;
    lastre = re;
    lastraddr = raddr;
    lastwe = we;
    lastwaddr = waddr;
    lastwdata = wdata;
}

int main(int argc, char **argv) {
    const char *vcdname = "sim_trace.vcd";
    const char *imemname = NULL;
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
                fprintf(stderr, "error: -im requires argument\n");
                return -1;
            }
            imemname = argv[2];
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

    if (imemname) {
        /* load memory from .hex file */
        FILE *fp = fopen(imemname, "r");
        if (!fp) {
            fprintf(stderr, "cannot open '%s' for reading\n", imemname);
            return -1;
        }

        char line[256];
        uint16_t addr = 0;
        while (fgets(line, sizeof(line), fp)) {
            uint32_t data;
            int ret = sscanf(line, "%x", &data);
            if (ret != 1)
                break;

            imemory[addr] = data & 0xffff;
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

        /* check for instruction memory */
        imem_transaction(sim->clk, 1, sim->iaddr, &sim->idata);

        /* check for data memory */
        dmem_transaction(sim->clk,
            sim->re, sim->raddr, &sim->rdata,
            sim->we, sim->waddr, sim->wdata);

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
        write(fd, dmemory, sizeof(dmemory));
        close(fd);
    }

    return 0;
}

