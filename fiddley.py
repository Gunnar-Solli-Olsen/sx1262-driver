import LoRa
import serial
import RPi.GPIO as GPIO
import time
lora = LoRa.LoRa(debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0") # please work

BAUDs = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200] # THESE DON'T APPLY IF YOU TRY CHANGING AWAY FROM 9600
BAUDs.sort(reverse=True)
# for baud in BAUDs:
        
#     #lora.lora_node.get_settings()
#     print(f"Changing to {baud}")
#     lora.change_settings(uart_baudrate=baud)
lora.change_settings(uart_baudrate=9600)

while True:
    lora.raw_send(65535, b'NOISE')

# GPIO.setmode(GPIO.BCM)

# GPIO.setup(22, GPIO.OUT)
# GPIO.setup(27, GPIO.OUT)

# GPIO.output(22, GPIO.HIGH)
# GPIO.output(27, GPIO.HIGH)
