#ifndef FILTER_H
#define FILTER_H

#include <stdint.h>

#include "config.h"

#define FILTER_NONE 0U
#define FILTER_MOVING_AVERAGE 1U
#define FILTER_FIR 2U

typedef struct {
    uint8_t mode;
    uint8_t window_size;
    uint16_t samples[FILTER_MOVING_AVERAGE + 2U];
    uint8_t index;
} fir_filter_state_t;

void filter_init(void);
void filter_set_mode(uint8_t mode);
uint16_t filter_process_sample(uint16_t input);

#endif
