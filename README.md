# Driver for using the waveshare sx126x - lora hats.

Code tested with the Waveshare SX1262-868M LoRa HAT

sx126x.py controls setup and usage of the transmitter, LoRa.py contains some utility functions and a basic (probably broken) messaging function.

For continuous messaging (e.g. lora.raw_send() in a while loop) make sure that the UART baud rate is higher than the air speed of the messages, otherwise the internal buffer on the HAT will fill leading to corrupted messages.