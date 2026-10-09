#include "protocol.h"

#include <avr/interrupt.h>
#include <avr/io.h>

uint16_t protocol_crc16_ccitt(const uint8_t *data, uint16_t length) {
    uint16_t crc = 0xFFFFU;
    for (uint16_t i = 0; i < length; ++i) {
        crc ^= (uint16_t)data[i] << 8U;
        for (uint8_t bit = 0; bit < 8U; ++bit) {
            if (crc & 0x8000U) {
                crc = (uint16_t)((crc << 1U) ^ 0x1021U);
            } else {
                crc <<= 1U;
            }
        }
    }
    return crc;
}

void protocol_encode_frame(uint8_t kind, const uint8_t *payload, uint16_t length, uint8_t *output) {
    if (output == (uint8_t *)0) {
        return;
    }
    if (payload == (const uint8_t *)0) {
        return;
    }
    if (length > PROTOCOL_MAX_PAYLOAD) {
        length = PROTOCOL_MAX_PAYLOAD;
    }
    output[0] = PROTOCOL_SYNC;
    output[1] = kind;
    output[2] = (uint8_t)(length & 0xFFU);
    output[3] = (uint8_t)((length >> 8U) & 0xFFU);
    for (uint16_t i = 0; i < length; ++i) {
        output[4U + i] = payload[i];
    }
    uint16_t crc = protocol_crc16_ccitt(output, 4U + length);
    output[4U + length] = (uint8_t)(crc & 0xFFU);
    output[5U + length] = (uint8_t)((crc >> 8U) & 0xFFU);
}

void protocol_send_frame(uint8_t kind, const uint8_t *payload, uint16_t length) {
    uint8_t frame[4U + PROTOCOL_MAX_PAYLOAD + 2U];
    protocol_encode_frame(kind, payload, length, frame);
    uart_write_block(frame, 4U + length + 2U);
}
