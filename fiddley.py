import LoRa
import serial
import RPi.GPIO as GPIO
import time
import sys

if "-s" in sys.argv:
    lora = LoRa.LoRa(CHANNEL=10000, debug=True, info=True, uart_baudrate=2400, air_speed=1200, SERIAL_PORT="/dev/ttyAMA0", rssi=False, timeout=2.0) 
    msg_count = 0

    lora.raw_send(20000, b"test")
     
else:
    lora = LoRa.LoRa(CHANNEL=20000, debug=True, info=True, uart_baudrate=2400, air_speed=1200, SERIAL_PORT="/dev/ttyAMA0", rssi=False, timeout=2.0) 
    msg_count = 0
    while True:
        input()
        packet = lora.raw_recv()
        # print(lora.lora_node.ser)
        if packet != None:
            msg_count+=1
            print(packet)
            print(f"msg_count: {msg_count}")
            
