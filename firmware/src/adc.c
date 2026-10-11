#include "adc.h"

#include <avr/io.h>

static uint8_t g_adc_channel = ADC_CHANNEL_DEFAULT;

void adc_init(uint8_t channel, uint8_t reference, uint8_t prescaler) {
    g_adc_channel = channel <= 5U ? channel : ADC_CHANNEL_DEFAULT;
    if (reference > 3U) {
        reference = ADC_REFERENCE_DEFAULT;
    }
    ADMUX = (uint8_t)((reference << REFS0) | g_adc_channel);
    ADCSRA = (uint8_t)((1U << ADEN) | (1U << ADIE) | (prescaler & 0x07U));
    ADCSRB = 0U;
}

void adc_disable(void) {
    ADCSRA &= (uint8_t)~(1U << ADEN);
}

void adc_start_conversion(void) {
    ADCSRA |= (1U << ADSC);
}

uint16_t adc_read_raw(void) {
    return ADCW;
}

bool adc_is_conversion_complete(void) {
    return (ADCSRA & (1U << ADIF)) != 0U;
}

void adc_set_channel(uint8_t channel) {
    if (channel > 5U) {
        return;
    }
    g_adc_channel = channel;
    ADMUX = (ADMUX & 0xF0U) | g_adc_channel;
}
