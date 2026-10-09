#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdint.h>
#include <stdbool.h>

#include "adc.h"
#include "buffer.h"
#include "config.h"
#include "protocol.h"
#include "timer.h"
#include "uart.h"

sample_buffer_t g_sample_buffer;
volatile bool g_acquisition_active = false;
volatile uint32_t g_sample_counter = 0U;

static void send_device_info(void) {
    uint8_t payload[8] = {
        0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00
    };
    payload[0] = 0x01U;
    payload[1] = (uint8_t)(F_CPU / 1000000UL);
    payload[2] = 0x0AU;
    payload[3] = SAMPLE_BUFFER_SIZE & 0xFFU;
    payload[4] = (SAMPLE_BUFFER_SIZE >> 8U) & 0xFFU;
    protocol_send_frame(PROTOCOL_TYPE_DEVICE_INFO, payload, 8U);
}

ISR(ADC_vect) {
    uint16_t sample = ADCW;
    if (g_acquisition_active) {
        buffer_push(&g_sample_buffer, sample);
        g_sample_counter += 1U;
        if (g_sample_buffer.sample_count >= SAMPLE_BUFFER_SIZE) {
            g_acquisition_active = false;
        }
    }
}

ISR(TIMER1_COMPA_vect) {
    if (g_acquisition_active) {
        adc_start_conversion();
    }
}

static void handle_command(uint8_t command, const uint8_t *payload, uint16_t len) {
    (void)payload;
    (void)len;
    switch (command) {
        case 0x10U:
            g_acquisition_active = true;
            buffer_reset(&g_sample_buffer);
            g_sample_counter = 0U;
            break;
        case 0x11U:
            g_acquisition_active = false;
            break;
        case 0x12U:
            if (len >= 2U) {
                uint32_t value = ((uint32_t)payload[0]) | (((uint32_t)payload[1]) << 8U);
                timer_set_sampling_frequency(value);
            }
            break;
        case 0x13U:
            if (len >= 1U) {
                adc_set_channel(payload[0]);
            }
            break;
        case 0x14U:
            send_device_info();
            break;
        default:
            break;
    }
}

int main(void) {
    cli();
    buffer_init(&g_sample_buffer);
    uart_init(UART_BAUD_RATE);
    adc_init(ADC_CHANNEL_DEFAULT, ADC_REFERENCE_DEFAULT, ADC_PRESCALER_DEFAULT);
    timer_init();
    timer_set_sampling_frequency(9600UL);
    sei();

    send_device_info();

    while (1) {
        if (g_sample_buffer.sample_count > 0U) {
            uint8_t payload[SAMPLE_BUFFER_SIZE * 2U];
            uint16_t count = g_sample_buffer.sample_count;
            uint16_t bytes_written = 0U;
            for (uint16_t i = 0; i < count; ++i) {
                uint16_t sample = buffer_peek(&g_sample_buffer, i);
                payload[bytes_written++] = (uint8_t)(sample & 0xFFU);
                payload[bytes_written++] = (uint8_t)((sample >> 8U) & 0xFFU);
            }
            protocol_send_frame(PROTOCOL_TYPE_ADC_BLOCK, payload, bytes_written);
            buffer_reset(&g_sample_buffer);
        }
    }

    return 0;
}
