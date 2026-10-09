#include "timer.h"

#include <avr/interrupt.h>
#include <avr/io.h>

static volatile uint32_t g_timer_sampling_frequency_hz = 9600UL;

void timer_init(void) {
    TCCR1A = 0;
    TCCR1B = (1U << WGM12) | (1U << CS10);
    OCR1A = 0;
    TIMSK1 = (1U << OCIE1A);
}

void timer_set_sampling_frequency(uint32_t fs_hz) {
    g_timer_sampling_frequency_hz = fs_hz;
    if (fs_hz == 0UL) {
        return;
    }
    uint32_t timer_ticks = (F_CPU / (2UL * fs_hz)) - 1UL;
    if (timer_ticks > 65535UL) {
        timer_ticks = 65535UL;
    }
    OCR1A = (uint16_t)timer_ticks;
}

uint32_t timer_get_sampling_frequency(void) {
    return g_timer_sampling_frequency_hz;
}

void timer_start(void) {
    TCCR1B |= (1U << CS10);
}

void timer_stop(void) {
    TCCR1B &= ~((1U << CS10) | (1U << CS11) | (1U << CS12));
}

ISR(TIMER1_COMPA_vect) {
    asm volatile("nop");
}
