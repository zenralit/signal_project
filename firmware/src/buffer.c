#include "buffer.h"

#include <avr/interrupt.h>

void buffer_init(sample_buffer_t *buffer) {
    buffer->head = 0U;
    buffer->tail = 0U;
    buffer->overflow = 0U;
}

void buffer_reset(sample_buffer_t *buffer) {
    uint8_t interrupt_state = SREG;
    cli();
    buffer->head = 0U;
    buffer->tail = 0U;
    buffer->overflow = 0U;
    SREG = interrupt_state;
}

bool buffer_push(sample_buffer_t *buffer, uint16_t sample) {
    uint8_t next = (uint8_t)(buffer->head + 1U);
    if (next == buffer->tail) {
        buffer->overflow = 1U;
        return false;
    }
    buffer->data[buffer->head] = sample;
    buffer->head = next;
    return true;
}

bool buffer_pop(sample_buffer_t *buffer, uint16_t *sample) {
    uint8_t interrupt_state = SREG;
    cli();
    if (buffer->tail == buffer->head) {
        SREG = interrupt_state;
        return false;
    }
    *sample = buffer->data[buffer->tail];
    buffer->tail = (uint8_t)(buffer->tail + 1U);
    SREG = interrupt_state;
    return true;
}

bool buffer_has_data(const sample_buffer_t *buffer) {
    uint8_t interrupt_state = SREG;
    cli();
    bool has_data = buffer->tail != buffer->head;
    SREG = interrupt_state;
    return has_data;
}

uint8_t buffer_count(const sample_buffer_t *buffer) {
    uint8_t interrupt_state = SREG;
    cli();
    uint8_t count = (uint8_t)(buffer->head - buffer->tail);
    SREG = interrupt_state;
    return count;
}

bool buffer_take_overflow(sample_buffer_t *buffer) {
    uint8_t interrupt_state = SREG;
    cli();
    bool overflowed = buffer->overflow != 0U;
    buffer->overflow = 0U;
    SREG = interrupt_state;
    return overflowed;
}
