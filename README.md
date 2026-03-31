# Driver for using the waveshare sx126x - lora hats.

sx126x.py controls setup and usage of the Waveshare SX1262-868M LoRa HAT, LoRa.py contains some utility functions and a basic (probably broken) messaging function. The driver works with point to point transmissions, and includes a header with the sender's address, and length of message. 

For continuous messaging (e.g. lora.raw_send() in a while loop) make sure that the UART baud rate is higher than the air speed of the messages, otherwise the internal buffer on the HAT will fill leading to corrupted messages. Note that continuous means sending individual 240 byte messages, not writing an arbitrary length bytearray. Behaviour for writing messages longer than the dividing packet length is untested. 

# Files
- sx126x.py : Driver for Waveshare sx126x series lora hats that do not support LoRaWAN
- LoRa.py : Abstraction layer with functions simplifying sending messages with the lora device

# Current working features

- An assortment airspeed bitrates
- Selecting UART baudrates other than 9600

- Direct transmission mode (relay mode does not work)
- Point to point transmission

- rssi noise and packet strength check

- Sending and receiving messages with the 240 byte-limit (less is untested)

# Common issues
- slower UART BAUDRATE than Air Rate on receiving node will lead to buffer overflows, this presents itself in the form of misshaped and mangled packets. The length header will be missed when reading malformed packets, causing issues.
- Different air rate applied than given during instantiation of sx126x, the E22-900T22S transmitter does not support the spreading factor required for the lower Air Rates (300bps and 1200bps), waveshare has as of 23.03.2026 not corrected the storefront description and documentation. The chip returns the air rate to the default value (2400bps).
- Driver supports point to point transmission mode.

# TODO

- Automatic splitting of bytestrings longer than message size, so that messages aren't cut off on the senders side.
- Add support for transparent transmission mode
- Add support for relay mode