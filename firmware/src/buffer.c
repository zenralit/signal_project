#include "buffer.h"

void buffer_init(sample_buffer_t *buffer) {
    if (buffer == (void *)0) {
        return;
    }
    for (uint16_t i = 0; i < SAMPLE_BUFFER_SIZE; ++i) {
        buffer->data[i] = 0U;
    }
    buffer->write_index = 0U;
    buffer->sample_count = 0U;
    buffer->full = false;
}

void buffer_push(sample_buffer_t *buffer, uint16_t sample) {
    if (buffer == (void *)0) {
        return;
    }
    buffer->data[buffer->write_index] = sample;
    buffer->write_index = (buffer->write_index + 1U) % SAMPLE_BUFFER_SIZE;
    if (buffer->sample_count < SAMPLE_BUFFER_SIZE) {
        buffer->sample_count += 1U;
    } else {
        buffer->full = true;
    }
}

uint16_t buffer_peek(const sample_buffer_t *buffer, uint16_t index) {
    if (buffer == (void *)0 || index >= SAMPLE_BUFFER_SIZE) {
        return 0U;
    }
    return buffer->data[index];
}

uint16_t buffer_count(const sample_buffer_t *buffer) {
    if (buffer == (void *)0) {
        return 0U;
    }
    return buffer->sample_count;
}

void buffer_reset(sample_buffer_t *buffer) {
    if (buffer == (void *)0) {
        return;
    }
    buffer_init(buffer);
}
