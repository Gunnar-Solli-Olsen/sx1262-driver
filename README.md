# Driver for using the waveshare SX1262-868M LoRa HAT

sx126x.py controls setup and usage of the Waveshare SX1262-868M LoRa HAT, LoRa.py contains some utility functions and a basic (probably broken) messaging function. The driver works with point to point transmissions, and includes a header with the length of message to improve performance when reading message from serial buffer. 

For continuous messaging (e.g. lora.raw_send() in a while loop) make sure that the UART baud rate is higher than the air speed of the messages, otherwise the internal buffer on the HAT will fill leading to corrupted messages. Note that continuous means sending individual 240 byte messages, not writing an arbitrary length bytearray. Behaviour for writing messages longer than the dividing packet length is untested. 

# Files
- sx126x.py : Driver for Waveshare sx126x series lora hats that do not support LoRaWAN
- LoRa.py : Abstraction layer with functions simplifying sending messages with the lora device

# Current working features

- Air bitrates between 2400 and 62500 kbps (actual constant throughput performance is lower)
- Selecting UART baudrates other than 9600
- Direct transmission mode (relay mode does not work)
- Point to point transmission
- Retreiveing currently applied configuration
- rssi noise and packet strength check
- Sending and receiving messages with the 240 byte-limit (less is untested)

# Common issues
- slower UART BAUDRATE than Air Rate on receiving node will lead to buffer overflows, this presents itself in the form of misshaped and mangled packets. The length header will be missed when reading malformed packets, causing issues.
- Different air rate applied than given during instantiation of sx126x, the E22-900T22S transmitter does not support the spreading factors required for the lower Air Rates (300bps and 1200bps), waveshare has as of 12.04.2026 corrected the storefront description, but not documentation. Ebyte has more correct documentation for their E22-xxxT22S series chips.
- Driver supports point to point transmission mode, sx126x.py can be instantiated in transparent transmission mode if you use it without LoRa.py

# TODO

- Automatic splitting of bytestrings longer than message size, so that messages aren't cut off on the senders side. 
- Add full support for transparent transmission mode
- Add support for relay mode