CC ?= cc
CFLAGS ?= -std=c11 -O2 -Wall -Wextra -Wpedantic -Werror
TARGET := test_min
TEST_SOURCE := ../tests/test_min.c

.PHONY: all test clean

all: $(TARGET)

$(TARGET): min.c min.h $(TEST_SOURCE)
	$(CC) $(CFLAGS) -I. min.c $(TEST_SOURCE) -o $(TARGET)

test: $(TARGET)
	./$(TARGET)

clean:
	$(RM) $(TARGET)
