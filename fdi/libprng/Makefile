CC?=arm-linux-gnueabihf-gcc
CFLAGS=-O2 -fPIC
all: libprng.so

libprng.so: prng.o
	$(CC) -shared -o $@ $^

prng.o: prng.c prng.h
	$(CC) $(CFLAGS) -c prng.c

clean:
	rm -f *.o libprng.so
