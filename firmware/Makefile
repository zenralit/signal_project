MCU = atmega328p
CC = avr-gcc
OBJCOPY = avr-objcopy
CFLAGS = -Wall -Wextra -Os -mmcu=$(MCU) -DF_CPU=16000000UL -Iinclude
LDFLAGS = -mmcu=$(MCU)

SRCDIR = src
INCDIR = include
BUILD_DIR = build

SOURCES = $(wildcard $(SRCDIR)/*.c)
OBJECTS = $(patsubst $(SRCDIR)/%.c,$(BUILD_DIR)/%.o,$(SOURCES))
TARGET = $(BUILD_DIR)/nawscope.hex

all: $(TARGET)

$(BUILD_DIR):
	@mkdir -p $(BUILD_DIR)

$(BUILD_DIR)/%.o: $(SRCDIR)/%.c | $(BUILD_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

$(TARGET): $(OBJECTS)
	$(CC) $(LDFLAGS) $(OBJECTS) -o $(BUILD_DIR)/nawscope.elf
	$(OBJCOPY) -O ihex -R .eeprom $(BUILD_DIR)/nawscope.elf $@

clean:
	rm -rf $(BUILD_DIR)

.PHONY: all clean
