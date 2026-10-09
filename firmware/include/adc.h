#ifndef ADC_H
#define ADC_H

#include <stdint.h>
#include <stdbool.h>

#include "config.h"

void adc_init(uint8_t channel, uint8_t reference, uint8_t prescaler);
void adc_disable(void);
void adc_start_conversion(void);
uint16_t adc_read_raw(void);
bool adc_is_conversion_complete(void);
void adc_set_channel(uint8_t channel);
void adc_set_sampling_rate(uint32_t fs_hz);

#endif
