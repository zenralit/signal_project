#ifndef BUFFER_H
#define BUFFER_H

#include <stdint.h>
#include <stdbool.h>

#include "config.h"

typedef struct {
    uint16_t data[SAMPLE_BUFFER_SIZE];
    volatile uint16_t write_index;
    volatile uint16_t sample_count;
    volatile bool full;
} sample_buffer_t;

void buffer_init(sample_buffer_t *buffer);
void buffer_push(sample_buffer_t *buffer, uint16_t sample);
uint16_t buffer_peek(const sample_buffer_t *buffer, uint16_t index);
uint16_t buffer_count(const sample_buffer_t *buffer);
void buffer_reset(sample_buffer_t *buffer);

#endif
