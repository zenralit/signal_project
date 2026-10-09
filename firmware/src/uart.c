#include "uart.h"

#include <avr/io.h>

#define UART_UBRR_VALUE(baud) ((F_CPU / (16UL * (baud))) - 1UL)

static volatile uint8_t g_tx_buffer[UART_TX_BUFFER_SIZE];
static volatile uint16_t g_tx_head = 0U;
static volatile uint16_t g_tx_tail = 0U;

void uart_init(uint32_t baudrate) {
    uint16_t ubrr = (uint16_t)UART_UBRR_VALUE(baudrate);
    UBRR0H = (uint8_t)(ubrr >> 8U);
    UBRR0L = (uint8_t)(ubrr & 0xFFU);
    UCSR0A = 0;
    UCSR0B = (1U << TXEN0) | (1U << TXCIE0);
    UCSR0C = (1U << UCSZ01) | (1U << UCSZ00);
}

void uart_write_byte(uint8_t value) {
    uint16_t next = (g_tx_head + 1U) % UART_TX_BUFFER_SIZE;
    if (next == g_tx_tail) {
        return;
    }
    g_tx_buffer[g_tx_head] = value;
    g_tx_head = next;
    if (UCSR0A & (1U << UDRE0)) {
        UDR0 = g_tx_buffer[g_tx_tail];
        g_tx_tail = (g_tx_tail + 1U) % UART_TX_BUFFER_SIZE;
    }
}

void uart_write_block(const uint8_t *data, uint16_t length) {
    if (data == (const uint8_t *)0 || length == 0U) {
        return;
    }
    for (uint16_t i = 0; i < length; ++i) {
        uart_write_byte(data[i]);
    }
}

uint8_t uart_tx_ready(void) {
    return g_tx_head != g_tx_tail;
}

void uart_flush(void) {
    while (g_tx_head != g_tx_tail) {
        UDR0 = g_tx_buffer[g_tx_tail];
        g_tx_tail = (g_tx_tail + 1U) % UART_TX_BUFFER_SIZE;
    }
}

ISR(USART_UDRE_vect) {
    if (g_tx_head != g_tx_tail) {
        UDR0 = g_tx_buffer[g_tx_tail];
        g_tx_tail = (g_tx_tail + 1U) % UART_TX_BUFFER_SIZE;
    }
}
