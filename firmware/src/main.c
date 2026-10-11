#include <avr/interrupt.h>
#include <avr/io.h>
#include <stdbool.h>
#include <stdint.h>

#include "adc.h"
#include "buffer.h"
#include "config.h"
#include "protocol.h"
#include "timer.h"
#include "uart.h"

static sample_buffer_t g_sample_buffer;
static volatile bool g_acquisition_active;
static uint16_t g_block_sequence;

static void send_device_info(void) {
    uint8_t payload[8] = {
        1U,
        0U,
        (uint8_t)(SAMPLE_RATE_DEFAULT_HZ & 0xFFU),
        (uint8_t)(SAMPLE_RATE_DEFAULT_HZ >> 8U),
        ADC_CHANNEL_DEFAULT,
        10U,
        (uint8_t)SAMPLE_BUFFER_SIZE,
        (uint8_t)(SAMPLE_BUFFER_SIZE >> 8U)
    };
    protocol_send_frame(PROTOCOL_TYPE_DEVICE_INFO, payload, sizeof(payload));
}

static void handle_command(const protocol_frame_t *frame) {
    if (frame->kind != PROTOCOL_TYPE_COMMAND || frame->payload_length == 0U) {
        return;
    }
    const uint8_t *payload = frame->payload;
    uint8_t command = payload[0];
    uint8_t argument_length = (uint8_t)(frame->payload_length - 1U);

    switch (command) {
        case PROTOCOL_COMMAND_START:
            g_acquisition_active = false;
            timer_stop();
            buffer_reset(&g_sample_buffer);
            g_block_sequence = 0U;
            g_acquisition_active = true;
            timer_start();
            break;
        case PROTOCOL_COMMAND_STOP:
            g_acquisition_active = false;
            timer_stop();
            break;
        case PROTOCOL_COMMAND_SET_SAMPLING_RATE:
            if (argument_length >= 2U) {
                uint16_t requested = (uint16_t)payload[1] | ((uint16_t)payload[2] << 8U);
                (void)timer_set_sampling_frequency(requested);
            }
            break;
        case PROTOCOL_COMMAND_SET_ADC_CHANNEL:
            if (argument_length >= 1U) {
                adc_set_channel(payload[1]);
            }
            break;
        case PROTOCOL_COMMAND_DEVICE_INFO:
            send_device_info();
            break;
        default: {
            uint8_t error_code = 1U;
            protocol_send_frame(PROTOCOL_TYPE_ERROR, &error_code, 1U);
            break;
        }
    }
}

static void transmit_sample_block(void) {
    uint8_t payload[PROTOCOL_MAX_PAYLOAD];
    uint8_t sample_count = 0U;
    uint16_t sample;
    uint16_t sampling_frequency_hz = (uint16_t)timer_get_sampling_frequency();
    payload[0] = (uint8_t)(sampling_frequency_hz & 0xFFU);
    payload[1] = (uint8_t)(sampling_frequency_hz >> 8U);
    payload[2] = (uint8_t)(g_block_sequence & 0xFFU);
    payload[3] = (uint8_t)(g_block_sequence >> 8U);

    while (sample_count < ADC_BLOCK_MAX_SAMPLES && buffer_pop(&g_sample_buffer, &sample)) {
        payload[4U + (2U * sample_count)] = (uint8_t)(sample & 0xFFU);
        payload[5U + (2U * sample_count)] = (uint8_t)(sample >> 8U);
        sample_count += 1U;
    }
    if (sample_count > 0U) {
        protocol_send_frame(PROTOCOL_TYPE_ADC_BLOCK, payload, (uint8_t)(4U + 2U * sample_count));
        g_block_sequence += 1U;
    }
}

ISR(TIMER1_COMPA_vect) {
    if (g_acquisition_active) {
        adc_start_conversion();
    }
}

ISR(ADC_vect) {
    if (g_acquisition_active && !buffer_push(&g_sample_buffer, adc_read_raw())) {
        g_sample_buffer.overflow = 1U;
    }
}

int main(void) {
    protocol_parser_t command_parser;
    protocol_frame_t received_frame;
    uint8_t received_byte;

    cli();
    buffer_init(&g_sample_buffer);
    protocol_parser_init(&command_parser);
    uart_init(UART_BAUD_RATE);
    adc_init(ADC_CHANNEL_DEFAULT, ADC_REFERENCE_DEFAULT, ADC_PRESCALER_DEFAULT);
    timer_init();
    (void)timer_set_sampling_frequency(SAMPLE_RATE_DEFAULT_HZ);
    sei();

    send_device_info();

    while (1) {
        while (uart_read_byte(&received_byte)) {
            if (protocol_parser_feed(&command_parser, received_byte, &received_frame)) {
                handle_command(&received_frame);
            }
        }

        if (buffer_take_overflow(&g_sample_buffer)) {
            uint8_t error_code = 2U;
            protocol_send_frame(PROTOCOL_TYPE_ERROR, &error_code, 1U);
        }
        uint8_t queued_samples = buffer_count(&g_sample_buffer);
        if (queued_samples >= ADC_BLOCK_MAX_SAMPLES ||
            (!g_acquisition_active && queued_samples > 0U)) {
            transmit_sample_block();
        }
    }
}
