#include "adc.h"

#include <avr/interrupt.h>
#include <avr/io.h>

static volatile uint8_t g_adc_channel = ADC_CHANNEL_DEFAULT;
static volatile uint8_t g_adc_reference = ADC_REFERENCE_DEFAULT;
static volatile uint8_t g_adc_prescaler = ADC_PRESCALER_DEFAULT;
static volatile uint32_t g_adc_sampling_rate_hz = 9600UL;

void adc_init(uint8_t channel, uint8_t reference, uint8_t prescaler) {
    g_adc_channel = channel & 0x07U;
    g_adc_reference = reference & 0x03U;
    g_adc_prescaler = prescaler;

    ADMUX = (1U << REFS0) | (g_adc_channel & 0x07U);
    ADCSRA = (1U << ADEN) | (1U << ADSC) | (1U << ADIE);
    ADCSRA |= (g_adc_prescaler & 0x07U);
    ADCSRB = 0;
}

void adc_disable(void) {
    ADCSRA &= ~(1U << ADEN);
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
    g_adc_channel = channel & 0x07U;
    ADMUX = (ADMUX & 0xF0U) | g_adc_channel;
}

void adc_set_sampling_rate(uint32_t fs_hz) {
    g_adc_sampling_rate_hz = fs_hz;
}

ISR(ADC_vect) {
    uint16_t value = ADCW;
    (void)value;
}
