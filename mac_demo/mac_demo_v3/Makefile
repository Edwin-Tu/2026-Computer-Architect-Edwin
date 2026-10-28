CC      ?= gcc
CFLAGS  ?= -std=c11 -Wall -Wextra -Werror -O2
PYTHON  ?= python3
RV_GCC  ?= riscv64-elf-gcc

.PHONY: test test-c test-py check-riscv bench-model bench-host bench-unroll bench-latency bench-packed clean

test: test-c test-py

test-c: test_mac
	./test_mac

test_mac: test_mac.c mac.c mac.h
	$(CC) $(CFLAGS) -o $@ test_mac.c mac.c

test-py:
	$(PYTHON) -m unittest discover -s . -p "test_*.py" -v

check-riscv:
	$(RV_GCC) -march=rv32im -mabi=ilp32 -ffreestanding -O1 -c riscv_probe.c -I . -o riscv_probe.o
	$(PYTHON) -m unittest test_riscv_encoding -v

bench-model:
	$(PYTHON) -m benchmark.clock_model_report

bench-host: benchmark/host_timing.c mac.c mac.h
	$(CC) -std=c11 -O1 -Wall -Wextra -Werror -o host_timing benchmark/host_timing.c mac.c -I.
	./host_timing 1024 2000 15

bench-unroll:
	$(PYTHON) -c "from benchmark.dotbench import run_all, to_markdown; print(to_markdown(run_all(ratios=(1.0,1.1,1.2), unroll=4)))"

bench-latency:
	$(PYTHON) -c "from pipeline_model import compare_mac_latency as c; [print(r) for r in c(n=1024)]"

bench-packed:
	$(PYTHON) -c "from benchmark.packed import run_packed_all as r; [print(x) for x in r()]"

clean:
	rm -f test_mac host_timing riscv_probe.o
	rm -rf __pycache__ benchmark/__pycache__
