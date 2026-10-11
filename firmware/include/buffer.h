#ifndef BUFFER_H
#define BUFFER_H

#include <stdbool.h>
#include <stdint.h>

#include "config.h"

typedef struct {
    uint16_t data[SAMPLE_BUFFER_SIZE];
    volatile uint8_t head;
    volatile uint8_t tail;
    volatile uint8_t overflow;
} sample_buffer_t;

void buffer_init(sample_buffer_t *buffer);
void buffer_reset(sample_buffer_t *buffer);
bool buffer_push(sample_buffer_t *buffer, uint16_t sample);
bool buffer_pop(sample_buffer_t *buffer, uint16_t *sample);
bool buffer_has_data(const sample_buffer_t *buffer);
uint8_t buffer_count(const sample_buffer_t *buffer);
bool buffer_take_overflow(sample_buffer_t *buffer);

#endif
