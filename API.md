# API definition, Gunnar's LoRa driver

## Send
Blocking send, timeout configured on initializing LoRa

Parameters: 
- address (2 byte integer)
- data (bytestring)

## Receive
Non-blocking receive, returns None when nothing in receive buffer. This function checks if there is an incoming message. 

Does not distinguish between sources, simultanious messages will interfeer with each other. Data is verified using a checksum, incorrect data can be re-sent in cases of corrupt transmission.

## raw_send
Send single message. 

Parameters: 
- address (2 byte integer)
- data (bytestring)

There is no acknowledgement response to this message.

## raw_recv
Non-blocking receive, returns None when nothing in receive buffer. This function checks if there is an incoming message, and returns incoming bytes.

## Sleep
Sets LoRa device to deep sleep mode
This makes the device use less power. During deep sleep the device does not accept incoming transmissions.

## Wake 
Sets LoRa device to transmission mode, reenabling transmitting data.

<!-- Reinitialize to change settings?  -->