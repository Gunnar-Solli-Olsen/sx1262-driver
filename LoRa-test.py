import LoRa
import sys
import time

arg = sys.argv

def test_transfer(data):
    lora = LoRa.LoRa(CHANNEL=int(arg[1]), uart_baudrate=9600, air_speed=2400, timeout=None, debug=True, info=True)
    lora.lora_node.get_settings()
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


def test_combinations(addr_ping=10000, addr_pong=10001):
    lora = LoRa.LoRa(CHANNEL=addr_ping, timeout=None, debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0")
    # lora.lora_node.get_settings()
    # time.sleep(1)
    # iterate through list of varying settings, transfer data from device 1 to device 2 while recording time required
    # TODO: Make list of stuff that can be changed
    res = []
    freqs = [868] # 433 doesn't work unless you have the sx1268 433M
    BAUDs = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200] # THESE DON'T APPLY IF YOU TRY CHANGING AWAY FROM 9600
    BAUDs.sort(reverse=True)
    package_size = [32, 64, 128, 240] # TODO: add support for smaller packets
    power_states = [10, 13, 17, 22]
    air_speeds = [1200, 2400, 4800, 9600, 19200, 38400, 62500]
    air_speeds.sort(reverse=True)

    # The amount of dimensions is too big here, need to focus on the important ones initially ignoring freqs and package size.
    for air_speed in air_speeds:
        for power_state in power_states:
            for BAUD in BAUDs: # Unused until baud fix is available
                lora.change_settings(FREQ=868, power=power_state, uart_baudrate=BAUD, air_speed=air_speed)
                # time.sleep(2)
                time.sleep(0.1)
                print("sending with db", power_state, ", air_speed:", air_speed, "and BAUD:", BAUD)

                # DO EXPERIMENT
                res.append(( test_ping(lora, 10 ,addr_ping, addr_pong), air_speed, power_state, BAUD ))
    return res

def test_combo_recv(addr_ping=10000, addr_pong=10001):
    lora = LoRa.LoRa(CHANNEL=addr_pong, timeout=None, debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0")
    # lora.lora_node.get_settings()
    # time.sleep(1)
    # iterate through list of varying settings, transfer data from device 1 to device 2 while recording time required
    # TODO: Make list of stuff that can be changed
    
    BAUDs = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200] # THESE DON'T APPLY IF YOU TRY CHANGING AWAY FROM 9600
    BAUDs.sort(reverse=True)
    package_size = [32, 64, 128, 240] # TODO: add support for smaller packets
    power_states = [10, 13, 17, 22]
    air_speeds = [1200, 2400, 4800, 9600, 19200, 38400, 62500]
    air_speeds.sort(reverse=True)

    # The amount of dimensions is too big here, need to focus on the important ones initially ignoring freqs and package size.
    for air_speed in air_speeds:
        for power_state in power_states:
            for BAUD in BAUDs:
                lora.change_settings(FREQ=868, power=power_state, uart_baudrate=BAUD, air_speed=air_speed)
                time.sleep(0.1)
                print("receiving with db", power_state, ", air_speed:", air_speed, "and BAUD:", BAUD)
                test_pong(lora, 10)
                print("changing settings...")
            
def test_ping(lora:LoRa.LoRa, tot_time, addr_ping=10000, addr_pong=10001):
    data = lora.checksum(time.time_ns().to_bytes(8))
    num_pongs = 0
    starttime = time.time()
    deltatime = time.time() - starttime
    while deltatime < tot_time:
        # send ping
        lora.raw_send(addr_pong, data)
        # wait for pong
        while deltatime < tot_time: # This becomes problematic, unanswered pings might lead to hanging (no more pongs)
            deltatime = time.time() - starttime
            rec = lora.raw_recv() 
            if rec:
                num_pongs += 1
                break
    return (deltatime, num_pongs)

def test_pong(lora:LoRa.LoRa, tot_time, addr_ping=10000, addr_pong=10001):
    first = True
    starttime = time.time()
    deltatime = time.time() - starttime
    while deltatime < tot_time:                     # THIS IS FLAWED    |This code is flawed due to the initial 
        if first:                                   # THIS IS FLAWED    |ping being missed causing accumulating 
            starttime = time.time()                 # THIS IS FLAWED    |misstimings between ping and pong. 
        deltatime = time.time() - starttime
        # receive msg
        mirror = lora.raw_recv()
        if mirror:
            lora.raw_send(addr_ping, mirror)
            # mirror incoming message
            first = False

            # Maybe parse something within the ping? Test focus is on relative 
            # differences between different parameters, so the added overhead matters very little
            # Should the new parameters for pong side be set through message? 
            # ready message sent from pong to ping, then run test like previously?  

if "-s" in arg:  

    # if int(arg[3]) > 233:
    #     print("INFO: this message does not fit in a single LoRa message!")
    # if int(arg[3]) > 233 * 255:
    #     print("WARNING: THIS IS TOO BIG TO SEND")
    # if int(arg[3]) > 255:
    #     print("WARNING: integers above 255 cannot be converted into a single byte!")
        
    # data = bytearray()
    # for j in range(int(arg[4])):
    #     for i in range(int(arg[3])): 
    #         data += i.to_bytes()
    # send msg
    starttime = time.time_ns()
    # test_transfer(data)
    res = test_combinations()
    deltatime = time.time_ns() - starttime
    
    print("Total time: ", deltatime / 1000000000, "seconds")
    print(res)
    # test_transfer_raw(data)

else:
    test_combo_recv()
    # lora = LoRa.LoRa(CHANNEL=int(arg[1]), uart_baudrate=9600, air_speed=2400, timeout=None, debug=True, info=True)    # lora.lora_node.get_settings()
    # time.sleep(1)
    # lora.lora_node.get_settings()
    # #lora.change_settings(uart_baudrate=115200)
    # lora.lora_node.get_settings()
    # while True:
    #     # receive msg
    #     mirror = lora.receive()
    #     if mirror:
    #         #print("MIRROR", mirror)
    #         # mirror incoming message
    #         #lora.send(65535, mirror)
    #         break
    #     #time.sleep(0.1)