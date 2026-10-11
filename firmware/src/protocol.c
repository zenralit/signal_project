#include "protocol.h"

#include <string.h>

#include "uart.h"

uint16_t protocol_crc16_ccitt(const uint8_t *data, uint16_t length) {
    uint16_t crc = 0xFFFFU;
    for (uint16_t index = 0U; index < length; ++index) {
        crc ^= (uint16_t)data[index] << 8U;
        for (uint8_t bit = 0U; bit < 8U; ++bit) {
            if (crc & 0x8000U) {
                crc = (uint16_t)((crc << 1U) ^ 0x1021U);
            } else {
                crc <<= 1U;
            }
        }
    }
    return crc;
}

void protocol_parser_init(protocol_parser_t *parser) {
    parser->count = 0U;
    parser->expected_length = 0U;
}

bool protocol_parser_feed(protocol_parser_t *parser, uint8_t byte, protocol_frame_t *frame) {
    if (parser->count == 0U) {
        if (byte == PROTOCOL_SYNC) {
            parser->bytes[parser->count++] = byte;
        }
        return false;
    }

    parser->bytes[parser->count++] = byte;
    if (parser->count == 4U) {
        uint16_t payload_length = (uint16_t)parser->bytes[2] |
                                 ((uint16_t)parser->bytes[3] << 8U);
        if (payload_length > PROTOCOL_MAX_PAYLOAD) {
            protocol_parser_init(parser);
            return false;
        }
        parser->expected_length = (uint8_t)(6U + payload_length);
    }
    if (parser->expected_length == 0U || parser->count < parser->expected_length) {
        return false;
    }

    uint8_t payload_length = (uint8_t)(parser->expected_length - 6U);
    uint16_t expected_crc = protocol_crc16_ccitt(parser->bytes, (uint16_t)(4U + payload_length));
    uint16_t received_crc = (uint16_t)parser->bytes[4U + payload_length] |
                            ((uint16_t)parser->bytes[5U + payload_length] << 8U);
    bool valid = expected_crc == received_crc;
    if (valid) {
        frame->kind = parser->bytes[1];
        frame->payload_length = payload_length;
        if (payload_length > 0U) {
            memcpy(frame->payload, &parser->bytes[4], payload_length);
        }
    }
    protocol_parser_init(parser);
    return valid;
}

void protocol_send_frame(uint8_t kind, const uint8_t *payload, uint8_t length) {
    if (length > PROTOCOL_MAX_PAYLOAD || (length > 0U && payload == (const uint8_t *)0)) {
        return;
    }
    uint8_t frame[4U + PROTOCOL_MAX_PAYLOAD + 2U];
    frame[0] = PROTOCOL_SYNC;
    frame[1] = kind;
    frame[2] = length;
    frame[3] = 0U;
    for (uint8_t index = 0U; index < length; ++index) {
        frame[4U + index] = payload[index];
    }
    uint16_t crc = protocol_crc16_ccitt(frame, (uint16_t)(4U + length));
    frame[4U + length] = (uint8_t)(crc & 0xFFU);
    frame[5U + length] = (uint8_t)(crc >> 8U);
    uart_write_block(frame, (uint16_t)(6U + length));
}
