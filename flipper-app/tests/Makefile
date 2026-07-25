CC      = gcc
CFLAGS  = -Wall -Wextra -std=c11 -g -fsanitize=address,undefined
INCLUDE = -Imocks -I..

.PHONY: test clean
test: test_protocol
	./test_protocol

test_protocol: test_protocol.c ../protocol.c
	$(CC) $(CFLAGS) $(INCLUDE) -o $@ $^

clean:
	rm -f test_protocol
