#include "timer.h"

#include <avr/io.h>

static volatile uint32_t g_timer_sampling_frequency_hz = SAMPLE_RATE_DEFAULT_HZ;
#define TIMER1_PRESCALER 8UL

void timer_init(void) {
    TCCR1A = 0U;
    TCCR1B = (1U << WGM12);
    OCR1A = (uint16_t)((F_CPU / (TIMER1_PRESCALER * SAMPLE_RATE_DEFAULT_HZ)) - 1UL);
    TIMSK1 = (1U << OCIE1A);
}

bool timer_set_sampling_frequency(uint32_t fs_hz) {
    if (fs_hz < SAMPLE_RATE_MIN_HZ || fs_hz > SAMPLE_RATE_MAX_HZ) {
        return false;
    }
    uint32_t compare_value = (F_CPU / (TIMER1_PRESCALER * fs_hz)) - 1UL;
    OCR1A = (uint16_t)compare_value;
    g_timer_sampling_frequency_hz = F_CPU / (TIMER1_PRESCALER * (compare_value + 1UL));
    return true;
}

uint32_t timer_get_sampling_frequency(void) {
    return g_timer_sampling_frequency_hz;
}

void timer_start(void) {
    TCNT1 = 0U;
    TCCR1B = (TCCR1B & (uint8_t)~((1U << CS10) | (1U << CS12))) | (1U << CS11);
}

void timer_stop(void) {
    TCCR1B &= (uint8_t)~((1U << CS10) | (1U << CS11) | (1U << CS12));
}
