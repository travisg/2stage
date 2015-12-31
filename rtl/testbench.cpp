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
 * - allows tracefilename to be specified via -v
*/

#include <sys/types.h>
#include <unistd.h>
#include <fcntl.h>
#include <getopt.h>

#include "Vtestbench.h"
#include "verilated.h"
#include <verilated_vcd_c.h>

#ifdef TRACE
static vluint64_t now = 0;

double sc_time_stamp() {
    return now;
}
#endif

void usage(int argc, char **argv)
{
    fprintf(stderr, "usage: %s [options]\n", argv[0]);
    fprintf(stderr, "options:\n");
    fprintf(stderr, "\t-h,--help: this help\n");
    fprintf(stderr, "\t-c,--cycles <cycles>:   number of cycles to run before stopping\n");
    fprintf(stderr, "\t-n,--notrace:           do not output trace file\n");
    fprintf(stderr, "\t-v,--vcd <file>:        output trace file, default is trace.vcd\n");
    exit(1);
}

int main(int argc, char **argv) {
    const char *vcdname = "trace.vcd";
    uint64_t cycles = 0;
    bool trace = true;
    int fd;

    const struct option long_options[] = {
        {"help",   0,  0,  'h'},
        {"cycles",   1,  0,  'c'},
        {"notrace",   0,  0,  'n'},
        {"vcd",   1,  0,  'v'},
    };

    for (;;) {
        int option_index = 0;
        int c;

        c = getopt_long(argc, argv, "hc:nv:", long_options, &option_index);
        if (c == -1)
            break;

        switch (c) {
            case 'c':
                cycles = atoll(optarg);
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

    Verilated::commandArgs(argc, argv);
    Verilated::debug(0);
    Verilated::randReset(2);

    Vtestbench *testbench = new Vtestbench;
    testbench->clk = 0;

    VerilatedVcdC* tfp = 0;
    if (trace) {
        Verilated::traceEverOn(true);
        tfp = new VerilatedVcdC;
        testbench->trace(tfp, 99);
        tfp->open(vcdname);
    }

    while (!Verilated::gotFinish()) {
        testbench->clk = !testbench->clk;
        testbench->eval();
        now += 5;
        if (tfp) {
            tfp->dump(now);
        }
        if (testbench->clk == 0 && cycles > 0) {
            if (--cycles == 0)
                break;
        }
    }
    if (tfp)
        tfp->close();
    testbench->final();
    delete testbench;

    return 0;
}

