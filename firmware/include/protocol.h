#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdbool.h>
#include <stdint.h>

#include "config.h"

#define PROTOCOL_SYNC 0xA5U
#define PROTOCOL_TYPE_ADC_BLOCK 0x01U
#define PROTOCOL_TYPE_CONFIGURATION 0x02U
#define PROTOCOL_TYPE_MEASUREMENT 0x03U
#define PROTOCOL_TYPE_ERROR 0x04U
#define PROTOCOL_TYPE_DEVICE_INFO 0x05U
#define PROTOCOL_TYPE_COMMAND 0x06U

#define PROTOCOL_COMMAND_START 0x10U
#define PROTOCOL_COMMAND_STOP 0x11U
#define PROTOCOL_COMMAND_SET_SAMPLING_RATE 0x12U
#define PROTOCOL_COMMAND_SET_ADC_CHANNEL 0x13U
#define PROTOCOL_COMMAND_DEVICE_INFO 0x14U

typedef struct {
    uint8_t kind;
    uint8_t payload[PROTOCOL_MAX_PAYLOAD];
    uint8_t payload_length;
} protocol_frame_t;

typedef struct {
    uint8_t bytes[4U + PROTOCOL_MAX_PAYLOAD + 2U];
    uint8_t count;
    uint8_t expected_length;
} protocol_parser_t;

uint16_t protocol_crc16_ccitt(const uint8_t *data, uint16_t length);
void protocol_parser_init(protocol_parser_t *parser);
bool protocol_parser_feed(protocol_parser_t *parser, uint8_t byte, protocol_frame_t *frame);
void protocol_send_frame(uint8_t kind, const uint8_t *payload, uint8_t length);

#endif
