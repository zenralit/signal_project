#ifndef TIMER_H
#define TIMER_H

#include <stdint.h>
#include <stdbool.h>

#include "config.h"

void timer_init(void);
bool timer_set_sampling_frequency(uint32_t fs_hz);
uint32_t timer_get_sampling_frequency(void);
void timer_start(void);
void timer_stop(void);

#endif
