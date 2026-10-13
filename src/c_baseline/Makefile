CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror
TARGET := test_min

.PHONY: all test clean

all: $(TARGET)

$(TARGET): min.c min.h test_min.c
	$(CC) $(CFLAGS) min.c test_min.c -o $(TARGET)

test: $(TARGET)
	./$(TARGET)

clean:
	$(RM) $(TARGET)
