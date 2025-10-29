import LoRa
import sys
import time

arg = sys.argv

def test_transfer(data):
    lora = LoRa.LoRa(CHANNEL=10000, uart_baudrate=115200, air_speed=2400, timeout=None, debug=True, info=True)
    lora.lora_node.get_settings()
    starttime = time.time_ns()
    lora.send(10001, data)
    deltatime = time.time_ns() - starttime
    
    print("Time until response: ", deltatime / 1000000000, "seconds")

def test_send_raw():
    lora = LoRa.LoRa(CHANNEL=10001, uart_baudrate=57600, timeout=None, debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0")
    data = lora.checksum(time.time_ns().to_bytes(8))
    starttime = time.time_ns()
    lora.raw_send(10000, data)
    deltatime = time.time_ns() - starttime
    
    print("Time until message sent: ", deltatime / 1000000000, "seconds")

def test_mirror_raw():
    lora = LoRa.LoRa(CHANNEL=10000, uart_baudrate=57600, timeout=None, debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0")
    while True:
        # receive msg
        mirror = lora.raw_recv()
        if mirror:
            lora.raw_send(10000, mirror)


def test_combinations(addr_ping=10000, addr_pong=10001):
    # iterate through list of varying settings, transfer data from device 1 to device 2 while recording time required
    # TODO: Make list of stuff that can be changed
    res = []
    BAUDs = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200] #
    #BAUDs = [9600]
    # BAUDs.sort(reverse=True)
    package_size = [32, 64, 128, 240] # TODO: add support for smaller packets
    power_states = [10, 13, 17, 22]
    air_speeds = [1200, 2400, 4800, 9600, 19200, 38400, 62500]
    air_speeds.sort(reverse=True)
    
    lora = LoRa.LoRa(CHANNEL=addr_ping, timeout=2, uart_baudrate=BAUDs[-1] ,debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0")

    for BAUD in BAUDs:
        air_speed = air_speeds[5]# in air_speeds:
            # for power_state in power_states:
        lora.change_settings(FREQ=868, power=22, uart_baudrate=BAUD, air_speed=air_speed)
        print("sending with db", 22, ", air_speed:", air_speed, "and BAUD:", BAUD)
        while True:
            rec = lora.raw_recv()
            if rec:
                if b'READY' in rec:
                    for i in range (5):
                        lora.raw_send(addr_pong, b'READY_CONF')
                        time.sleep(0.2)
                    break
        time.sleep(2)
        #input()
        # DO EXPERIMENT
        res.append(( test_ping(lora, 10 ,addr_ping, addr_pong), air_speed, 22, BAUD ))
    return res

def test_combo_recv(addr_ping=10000, addr_pong=10001):
    # iterate through list of varying settings, transfer data from device 1 to device 2 while recording time required
    # TODO: Make list of stuff that can be changed
    
    BAUDs = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200] #
    #BAUDs = [9600]
    # BAUDs.sort(reverse=True)
    package_size = [32, 64, 128, 240] # TODO: add support for smaller packets
    power_states = [10, 13, 17, 22]
    air_speeds = [1200, 2400, 4800, 9600, 19200, 38400, 62500]
    air_speeds.sort(reverse=True)
    lora = LoRa.LoRa(CHANNEL=addr_pong, timeout=2, uart_baudrate=BAUDs[-1] ,debug=True, info=True, SERIAL_PORT="/dev/ttyUSB0")
    # lora.lora_node.get_settings()
    # time.sleep(1)

    # The amount of dimensions is too big here, need to focus on the important ones initially ignoring freqs and package size.
    for BAUD in BAUDs:
        air_speed = air_speeds[5]# in air_speeds:
        #     for power_state in power_states:
                    
        lora.change_settings(FREQ=868, power=22, uart_baudrate=BAUD, air_speed=air_speed)
        
        print("receiving with db", 22, ", air_speed:", air_speed, "and BAUD:", BAUD)

        start = False
        while not start:
            for i in range (5):
                lora.raw_send(addr_ping, b'READY')
                time.sleep(0.2)
            t0 = time.time()
            d = time.time() - t0
            while d < 5:
                d = time.time() - t0
                rec = lora.raw_recv()
                if rec:
                    print("baluba:", rec)
                    if b'READY_CONF' in rec:
                        start = True
                        break
        test_pong(lora)
            
def test_ping(lora:LoRa.LoRa, tot_time, addr_ping=10000, addr_pong=10001):
    data = b'123test' #lora.checksum(time.time_ns().to_bytes(8))
    num_pongs = 0
    starttime = time.time()
    deltatime = time.time() - starttime
    lora.lora_node.ser.reset_input_buffer()
    while deltatime < tot_time:
        # send ping
        lora.raw_send(addr_pong, data)
        # wait for pong
        while deltatime < tot_time:
            deltatime = time.time() - starttime
            rec = lora.raw_recv() 
            if rec:
                num_pongs += 1
                break
    for i in range (5):
        lora.raw_send(addr_pong, b'DONE')
        time.sleep(0.2)

    return (deltatime, num_pongs)

def test_pong(lora:LoRa.LoRa, addr_ping=10000, addr_pong=10001):
    Done = False
    lora.lora_node.ser.reset_input_buffer()# THIS MAKES THE SHIT WORK ARE YOU FUCKING WITH ME
    while not Done:                     
        # receive msg
        mirror = lora.raw_recv()
        if mirror:
            lora.raw_send(addr_ping, mirror)
            # mirror incoming message
            if b'DONE' in mirror:
                Done = True


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
    # test_send_raw()
    deltatime = time.time_ns() - starttime
    
    print("Total time: ", deltatime / 1000000000, "seconds")
    print(res)
    # test_transfer_raw(data)

else:
    test_combo_recv()
    # test_mirror_raw()

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