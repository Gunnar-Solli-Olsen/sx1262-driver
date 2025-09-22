import LoRa
import sys
import time

arg = sys.argv

def test_transfer(data):
    lora = LoRa.LoRa(CHANNEL=int(arg[1]), timeout=None, debug=True, info=True)
    starttime = time.time_ns()
    lora.send(10000, data)
    deltatime = time.time_ns() - starttime
    
    print("Time until response: ", deltatime / 1000000000, "seconds")

def test_transfer_raw(data):
    lora = LoRa.LoRa(CHANNEL=int(arg[1]), timeout=None, debug=True, info=True)
    starttime = time.time_ns()
    lora.raw_send(10000, data)
    deltatime = time.time_ns() - starttime
    
    print("Time until message sent: ", deltatime / 1000000000, "seconds")


def test_combinations():
    lora = LoRa.LoRa(CHANNEL=int(arg[1]), timeout=None, debug=True, info=True)
    # iterate through list of varying settings, transfer data from device 1 to device 2 while recording time required
    # TODO: Make list of stuff that can be changed

    freqs = [433, 868]
    BAUDs = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
    package_size = [32, 64, 128, 240] # TODO: add support for smaller packets
    power_states = [10, 13, 17, 22]
    air_speeds = [300, 1200, 2400, 4800, 9600, 19200, 38400, 62500]

    # The amount of dimensions is too big here, need to focus on the important ones initially ignoring freqs and package size.
    for air_speed in air_speeds:
        for power_state in power_states:
            for BAUD in BAUDs:
                # DO EXPERIMENT
                lora.change_settings(FREQ=freqs[1], power=power_state, uart_baudrate=BAUD, air_speed=air_speed)


    # Should the data be transmitted one way only, or should the data be mirrored? 

if "-s" in arg:  

    if int(arg[3]) > 233:
        print("INFO: this message does not fit in a single LoRa message!")
    if int(arg[3]) > 233 * 255:
        print("WARNING: THIS IS TOO BIG TO SEND")
    if int(arg[3]) > 255:
        print("WARNING: integers above 255 cannot be converted into a single byte!")
        
    data = bytearray()
    for j in range(int(arg[4])):
        for i in range(int(arg[3])): 
            data += i.to_bytes()
    # send msg
    starttime = time.time_ns()
    test_combinations()
    deltatime = time.time_ns() - starttime
    
    print("Time until all settings switched: ", deltatime / 1000000000, "seconds")

    # test_transfer_raw(data)

else:
    lora = LoRa.LoRa(CHANNEL=int(arg[1]), timeout=None, debug=True, info=True)
    while True:
        # receive msg
        mirror = lora.raw_recv()
        if mirror:
            print("MIRROR", mirror)
            # mirror incoming message
            #lora.send(65535, mirror)
            break
        time.sleep(0.1)
