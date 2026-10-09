#ifndef PROTOCOL_H
#define PROTOCOL_H

#include <stdint.h>
#include <stddef.h>

#define PROTOCOL_SYNC 0xA5U
#define PROTOCOL_TYPE_ADC_BLOCK 0x01U
#define PROTOCOL_TYPE_CONFIG 0x02U
#define PROTOCOL_TYPE_MEASUREMENT 0x03U
#define PROTOCOL_TYPE_ERROR 0x04U
#define PROTOCOL_TYPE_DEVICE_INFO 0x05U
#define PROTOCOL_TYPE_COMMAND 0x06U

#define PROTOCOL_MAX_PAYLOAD 64U

typedef struct {
    uint8_t kind;
    uint8_t payload[PROTOCOL_MAX_PAYLOAD];
    uint16_t payload_length;
} protocol_frame_t;

uint16_t protocol_crc16_ccitt(const uint8_t *data, uint16_t length);
void protocol_encode_frame(uint8_t kind, const uint8_t *payload, uint16_t length, uint8_t *output);
void protocol_send_frame(uint8_t kind, const uint8_t *payload, uint16_t length);

#endif
