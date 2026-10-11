#include "uart.h"

#include <avr/interrupt.h>
#include <avr/io.h>

#define UART_INDEX_MASK(size) ((size) - 1U)
#define UART_UBRR_VALUE(baud) (((F_CPU + (4UL * (baud))) / (8UL * (baud))) - 1UL)

static volatile uint8_t g_tx_buffer[UART_TX_BUFFER_SIZE];
static volatile uint8_t g_tx_head;
static volatile uint8_t g_tx_tail;
static volatile uint8_t g_rx_buffer[UART_RX_BUFFER_SIZE];
static volatile uint8_t g_rx_head;
static volatile uint8_t g_rx_tail;

void uart_init(uint32_t baudrate) {
    uint16_t ubrr = (uint16_t)UART_UBRR_VALUE(baudrate);
    UBRR0H = (uint8_t)(ubrr >> 8U);
    UBRR0L = (uint8_t)(ubrr & 0xFFU);
    UCSR0A = (1U << U2X0);
    UCSR0B = (1U << RXEN0) | (1U << TXEN0) | (1U << RXCIE0);
    UCSR0C = (1U << UCSZ01) | (1U << UCSZ00);
    g_tx_head = 0U;
    g_tx_tail = 0U;
    g_rx_head = 0U;
    g_rx_tail = 0U;
}

void uart_write_byte(uint8_t value) {
    uint8_t next = (uint8_t)(g_tx_head + 1U) & UART_INDEX_MASK(UART_TX_BUFFER_SIZE);
    while (next == g_tx_tail) {
        next = (uint8_t)(g_tx_head + 1U) & UART_INDEX_MASK(UART_TX_BUFFER_SIZE);
    }
    g_tx_buffer[g_tx_head] = value;
    g_tx_head = next;
    UCSR0B |= (1U << UDRIE0);
}

void uart_write_block(const uint8_t *data, uint16_t length) {
    if (data == (const uint8_t *)0) {
        return;
    }
    for (uint16_t index = 0U; index < length; ++index) {
        uart_write_byte(data[index]);
    }
}

bool uart_read_byte(uint8_t *value) {
    if (value == (uint8_t *)0 || g_rx_head == g_rx_tail) {
        return false;
    }
    *value = g_rx_buffer[g_rx_tail];
    g_rx_tail = (uint8_t)(g_rx_tail + 1U) & UART_INDEX_MASK(UART_RX_BUFFER_SIZE);
    return true;
}

ISR(USART_RX_vect) {
    uint8_t value = UDR0;
    uint8_t next = (uint8_t)(g_rx_head + 1U) & UART_INDEX_MASK(UART_RX_BUFFER_SIZE);
    if (next != g_rx_tail) {
        g_rx_buffer[g_rx_head] = value;
        g_rx_head = next;
    }
}

ISR(USART_UDRE_vect) {
    if (g_tx_head == g_tx_tail) {
        UCSR0B &= (uint8_t)~(1U << UDRIE0);
        return;
    }
    UDR0 = g_tx_buffer[g_tx_tail];
    g_tx_tail = (uint8_t)(g_tx_tail + 1U) & UART_INDEX_MASK(UART_TX_BUFFER_SIZE);
}
