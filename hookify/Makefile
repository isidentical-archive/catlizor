.PHONY: clean

hookify.so: hookify.c
	gcc `python-config --cflags` `python-config --includes` -Wl,--export-dynamic -fPIC -shared -o $@ $^ -ldl `python-config --libs`

clean:
	rm hookify.so
