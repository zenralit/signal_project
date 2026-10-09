#ifndef UART_H
#define UART_H

#include <stdint.h>
#include <stdbool.h>

#include "config.h"

void uart_init(uint32_t baudrate);
void uart_write_byte(uint8_t value);
void uart_write_block(const uint8_t *data, uint16_t length);
uint8_t uart_tx_ready(void);
void uart_flush(void);

#endif
