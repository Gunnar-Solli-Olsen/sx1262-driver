import LoRa
import sys
import time

arg = sys.argv
lora = LoRa.LoRa(CHANNEL=int(arg[1]), timeout=None, debug=True, info=True)

def test_transfer(data):

    starttime = time.time_ns()
    lora.send(10000, data)
    deltatime = time.time_ns() - starttime
    
    print("Time until response: ", deltatime / 1000000000, "seconds")

def test_transfer_raw(data):

    starttime = time.time_ns()
    lora.raw_send(10000, data)
    deltatime = time.time_ns() - starttime
    
    print("Time until message sent: ", deltatime / 1000000000, "seconds")


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
    test_transfer_raw(data)

else:
    while True:
        # receive msg
        mirror = lora.raw_recv()
        if mirror:
            print("MIRROR", mirror)
            # mirror incoming message
            #lora.send(65535, mirror)
            break
        time.sleep(0.1)
    
