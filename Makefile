# Makefile to wrap the install of platformio

VENVDIR = venv
VENVACTIVATE = $(VENVDIR)/bin/activate
FIRMWARE = .pio/build/mini/firmware.hex

all: build

install: $(VENVACTIVATE)

$(VENVACTIVATE): requirments.txt
	test -d $(VENVDIR) || python3 -m venv $(VENVDIR)
	. $(VENVACTIVATE) && \
	pip install wheel && \
	pip install -r requirments.txt && \
	touch $(VENVACTIVATE)

build: $(FIRMWARE)
	. $(VENVACTIVATE) && \
	pio run

upload: build
	. $(VENVACTIVATE) && \
	pio run -t upload

monitor:
	. $(VENVACTIVATE) && \
	pio device monitor

clean:
	echo "nop"

mrproper: clean
	rm -rf $(VENVDIR)
