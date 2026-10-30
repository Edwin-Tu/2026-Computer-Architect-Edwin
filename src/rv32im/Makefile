TOOLCHAIN_PREFIX ?= riscv64-elf-
AS = $(TOOLCHAIN_PREFIX)gcc
OBJDUMP = $(TOOLCHAIN_PREFIX)objdump
ARCH_FLAGS = -march=rv32im -mabi=ilp32
ASFLAGS ?= -g -Wall
TARGET = min_s32.o
DISASSEMBLY = min_s32.disasm.txt

.PHONY: all disasm clean

all: $(TARGET) $(DISASSEMBLY)

$(TARGET): min_s32.S
	$(AS) $(ARCH_FLAGS) $(ASFLAGS) -c $< -o $@

$(DISASSEMBLY): $(TARGET)
	$(OBJDUMP) -d -M no-aliases $< > $@

disasm: $(DISASSEMBLY)

clean:
	$(RM) $(TARGET) $(DISASSEMBLY)
