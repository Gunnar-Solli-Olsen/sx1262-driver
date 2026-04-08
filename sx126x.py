# This file is used for LoRa and Raspberry pi4B related issues 

import RPi.GPIO as GPIO
import serial
import time

class sx126x:

    M0 = 22
    M1 = 27
    AUX = 4
    # if the header is 0xC0, then the LoRa register settings dont lost when it poweroff, and 0xC2 will be lost. 
    cfg_reg = [0xC0,0x00,0x09,0x00,0x00,0x00,0x62,0x00,0x16,0x43,0x00,0x00]
    # cfg_reg = [0xC2,0x00,0x09,0x00,0x00,0x00,0x62,0x00,0x16,0x03,0x00,0x00] # What does 43 do? (looks like it is just overwritten) 0x43 is actually transparent transmission mode, these values are overwritten anyway so the point of these is questionable
    get_reg = bytes(12)
    rssi = False
    addr = 65535
    serial_n = ""
    addr_temp = 0
    prev_baud_rate = None
    #
    # start frequence of two lora module
    #
    # E22-400T22S           E22-900T22S
    # 410~493MHz      or    850~930MHz
    start_freq = 850 # Why is this here 

    #
    # offset between start and end frequence of two lora module
    #
    # E22-400T22S           E22-900T22S
    # 410~493MHz      or    850~930MHz
    offset_freq = 18

    SX126X_CONF_UART_BAUDRATE = 9600

    SX126X_UART_BAUDRATE = {
        1200 : 0x00,
        2400 : 0x20,
        4800 : 0x40,
        9600 : 0x60,
        19200 : 0x80,
        38400 : 0xA0,
        57600 : 0xC0,
        115200 : 0xE0
   }
    
    lora_air_speed_dic = {
        300:0x00,  #! only available on SX1268-433T22S
        1200:0x01, #! only available on SX1268-433T22S
        2400:0x02,
        4800:0x03,
        9600:0x04,
        19200:0x05,
        38400:0x06,
        62500:0x07
    }

    SX126X_PACKAGE_SIZE_240_BYTE = 0x00
    SX126X_PACKAGE_SIZE_128_BYTE = 0x40
    SX126X_PACKAGE_SIZE_64_BYTE = 0x80
    SX126X_PACKAGE_SIZE_32_BYTE = 0xC0

    lora_buffer_size_dic = {
        240:SX126X_PACKAGE_SIZE_240_BYTE,
        128:SX126X_PACKAGE_SIZE_128_BYTE,
        64:SX126X_PACKAGE_SIZE_64_BYTE,
        32:SX126X_PACKAGE_SIZE_32_BYTE
    }
    # what the hell is this, these constants are never used
    SX126X_Power_22dBm = 0x00
    SX126X_Power_17dBm = 0x01
    SX126X_Power_13dBm = 0x02
    SX126X_Power_10dBm = 0x03

    lora_power_dic = {
        22:0x00,
        17:0x01,
        13:0x02,
        10:0x03
    }


    def __init__(self,serial_num,freq,addr,power,rssi,prev_baud_rate:int|None=None, uart_baudrate=9600,air_speed=2400, net_id=0,buffer_size = 240,crypt=0,relay=False,point_to_point=True, lbt=False,wor=False, timeout:float|None=None, info:bool=False, warning:bool=True, debug:bool=False):
        """
        Params:
            serial_num (string): Serial port number (default "/dev/ttyAMA0" for RPi w. debian)
            freq (int): Frequency to use for transmission, 433 and 868 MHz are usable in the EU 
            addr (int): 2 byte address to use for device, incoming messages will be received with this address, and outgoing messages will include this address. (this does not apply to repeater mode, the bytes there are used to bridge networks) 
            power (int): transmission power in decibel, choose from these values [10, 13, 17, 22]    
            rssi (bool): Include signal noise information
            uart_baudrate (int): uart baud rate for transmissions, starts at 9600 as default. Note that this rate only applies to communication, not for configuration
            air_speed (int): air speed of transmissions, should be identical between sender and receiver
            net_id (int): network id, MUST BE IDENTICAL BETWEEN SENDER AND RECEIVER (use repeater mode to bridge between net ids)
            buffer_size (int): size of individual packets
            crypt (int): cryptographic key to be used for encrypting messages.
            lbt (bool): Enable or disable listen before talk (LBT)
            wor (bool): Enable or disable Wake on Radio

        """
        self.rssi = rssi
        self.addr = addr
        self.freq = freq
        self.serial_n = serial_num
        self.power = power
        self.baudrate = uart_baudrate
        self.timeout = timeout
        self.info = info
        self.warning = warning
        self.debug = debug
        self.point_to_point = point_to_point
        # Initial the GPIO for M0 and M1 Pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.M0,GPIO.OUT)
        GPIO.setup(self.M1,GPIO.OUT)
        GPIO.output(self.M0,GPIO.LOW)
        GPIO.output(self.M1,GPIO.HIGH)
        # ! AUX PIN IS 1 WHEN E22-900T22S SEND BUFFER IS EMPTY
        GPIO.setup(self.AUX,GPIO.IN) 
        time.sleep(0.1) # Sleep so device has time to react

        while GPIO.input(self.AUX) == 0:  
            time.sleep(0.01)
        # The hardware UART of Pi3B+,Pi4B is /dev/ttyS0 (or you can map it to another one manually if you are a nerd)
        self.ser = serial.Serial(serial_num, self.SX126X_CONF_UART_BAUDRATE, timeout=self.timeout)
        self.ser.flushInput()

        self.device_model = self.get_device_model()
        self.set(freq,addr,power,rssi,uart_baudrate=self.baudrate,air_speed=air_speed,net_id=net_id,buffer_size=buffer_size,crypt=crypt,relay=relay,point_to_point=self.point_to_point, lbt=lbt, wor=wor)

        self.ser.close()
        self.ser = serial.Serial(serial_num,uart_baudrate, timeout=self.timeout)
 

    def set(self,freq,addr,power,rssi,uart_baudrate=9600,air_speed=2400,\
            net_id=0,buffer_size = 240,crypt=0,\
            relay=False, point_to_point:bool=True,lbt=False,wor=False):
        self.addr = addr
        # We should pull up the M1 pin when sets the module
        GPIO.output(self.M0,GPIO.LOW)
        GPIO.output(self.M1,GPIO.HIGH)
        time.sleep(0.1) # wait for device to turn to configuration mode
        # TODO: Replace this sleep with smaller sleep and AT command to get current mode of device 
        # TODO: (see Ebyte documentation for AT commands)

        low_addr = addr & 0xff
        high_addr = addr >> 8 & 0xff
        net_id_temp = net_id & 0xff
        if self.debug: print(f"DEBUG: device model:{self.device_model}")

        # TODO: Use AT command to get other device models, this software is currently known to work with a single device so the first check could be to verify the return being "DEVTYPE=E22-900T22S", and throw exception when missmatches between frequency and used device is detected. 
        # ? AT command is not the only way to get the device model, C0 command also yields device name in last two bytes
        if self.device_model == b"E22-900T22S":

            if freq > 850: 
                freq_temp = freq - 850
                self.start_freq = 850
                self.offset_freq = freq_temp
                if self.debug: print(f"DEBUG: frequency: {freq} ({freq_temp})")
            else:
                raise Exception("Frequency outside valid range (850 to 930)", freq)
            
        elif self.device_model == b"E22-400T22S":
            raise Exception("This code is untested for the sx1268-433M")
            # print("WARNING: ")
            # freq_temp = freq - 410
            # self.start_freq  = 410
            # self.offset_freq = freq_temp 
        else:
            raise Exception(f"Device not recognized: {self.device_model}")
            
        # TODO: Add range checks for the selected frequency
        # TODO: Change the frequency selection so the developer gets warned when selecting invalid freq.
        if air_speed >= uart_baudrate:
            if self.warning: print("WARNING: Air Rate is equal or higher than baudrate, this can lead to receiver side buffer overflows (device receives data faster than it can send it to host)")

        air_speed_temp = self.lora_air_speed_dic.get(air_speed,None)
        if air_speed_temp is None:
            raise Exception("Air speed not recognized", air_speed)
        
        buffer_size_temp = self.lora_buffer_size_dic.get(buffer_size,None)
        if buffer_size_temp is None:
            raise Exception("Buffer size not recognized", buffer_size)
        
        power_temp = self.lora_power_dic.get(power,None)
        if power_temp is None:
            raise Exception("Transmission power not recognized", power)
        if self.debug: print(f"DEBUG: transmission power: {power}")
        
        if rssi: 
            # enable printing rssi values
            rssi_temp = 0x80  # This appends every message and has some performance impact 
        else:
            # disable print rssi value
            rssi_temp = 0x00        
        
        if rssi: # TODO: add separate value for rssi noise
            rssi_noise = 0x20 # This enables command {0xC0, 0xC1, 0xC2, 0xC3} in transmission and WoR modes to get current ambient noise
        else:
            rssi_noise = 0x00

        if point_to_point == True:
            # 0x40 enables point to point transmission
            transmission_mode = 0x40
        else:
            # 0x00 enables transparent transmission
            transmission_mode = 0x00 # ! THIS CHANGES WHAT MUST BE WRITTEN DURING SEND (and recv doesn't really need the sender address and net_id)
        if self.debug: print(f"DEBUG: point_to_point   : {point_to_point}")
        if self.debug: print(f"DEBUG: transmission_mode: {transmission_mode}")
        # get crypt
        l_crypt = crypt & 0xff
        h_crypt = crypt >> 8 & 0xff

        # TODO: Add support for transparent transmitting mode
        if relay==False:
            self.cfg_reg[3] = high_addr
            self.cfg_reg[4] = low_addr
            self.cfg_reg[5] = net_id_temp 
            # TODO: CHECK IF AIR RATE IS SUPPORTED BEFORE TRYING TO WRITE IT  (sx1262 868M changes 300 and 1200 to 2400)
            self.cfg_reg[6] = self.SX126X_UART_BAUDRATE[uart_baudrate] + air_speed_temp 
            # print((self.SX126X_UART_BAUDRATE[uart_baudrate] + air_speed_temp).to_bytes(1))
            self.cfg_reg[7] = buffer_size_temp + power_temp + rssi_noise 
            self.cfg_reg[8] = freq_temp 
            # 
            # The HAT will output a packet rssi value following received message
            # when the eighth bit with 06H register(rssi_temp = 0x80) is enabled
            #
            self.cfg_reg[9] = transmission_mode + 0x03 + rssi_temp 

            # WoR requires the sender to be manually set to sender, and receiver set to receiver.

            self.cfg_reg[10] = h_crypt
            self.cfg_reg[11] = l_crypt
            if self.info: print(f"INFO: Setting device config : {bytearray(self.cfg_reg)}")
        else:
            raise Exception("Relay mode has not been implemented yet")
            # TODO: Implement repeater mode
            #? ADDH and ADDL are used to relay messages between networks (as defined by NETID)
            #? Relay mode disables receiving and transmitting messages, the node only acts as a relay (this also disables low power mode)
            #? 
            # self.cfg_reg[3] = 0x01 # Why is the adress hardcoded for relay mode? 
            # self.cfg_reg[4] = 0x02
            # self.cfg_reg[5] = 0x03
            # self.cfg_reg[6] = self.SX126X_UART_BAUDRATE[uart_baudrate] + air_speed_temp
            # # 
            # # it will enable to read noise rssi value when add 0x20 as follow
            # # 
            # self.cfg_reg[7] = buffer_size_temp + power_temp + 0x20
            # self.cfg_reg[8] = freq_temp
            # #
            # # it will output a packet rssi value following received message
            # # when enable eighth bit with 06H register(rssi_temp = 0x80)
            # #
            # self.cfg_reg[9] = 0x03 + rssi_temp
            # self.cfg_reg[10] = h_crypt
            # self.cfg_reg[11] = l_crypt

        # TODO: Decide if we should warn or throw Exceptions about different configuration being returned on writing config

        cfg_reg_host = bytes(self.cfg_reg)
        written = self.ser.write(cfg_reg_host)
        if written != len(cfg_reg_host):
            if self.warning: print(f"WARNING: missmatch in amount of written bytes {len(cfg_reg_host)} != {written}")
        else: 
            r_buff = self.ser.read(12)
            # print(r_buff)
            if r_buff[1::] == cfg_reg_host[1::]:
                if self.info: print(f"SUCCESS: r_buff matches cfg_reg")
            else:
                if self.warning: print(f"WARNING: missmatch between written and returned configuration\nwritten : {cfg_reg_host}\nreceived: {r_buff}")
       
        # TODO: Rewrite this entire section, verify that settings have been applied correctly, read reply with timeout instead of using break and pass 
        # * Previous version of register configuration
        # for i in range(3):
        #     written = self.ser.write(bytes(self.cfg_reg)) # write config to registers
        #     while self.ser.out_waiting > 0:
        #         time.sleep(0.01)
        #     # print("Written: ", self.ser.out_waiting, "of", len(self.cfg_reg))

        #     # Wait longer during retries, this lowers the configuration time for higher baud-rates
        #     time.sleep(1+i*2) # wait for 1, 3, 5 seconds when applying settings

        #     if self.ser.inWaiting() > 0:
        #         time.sleep(0.5)
        #         r_buff = self.ser.read(self.ser.inWaiting()) # Read answer from buffer
        #         if r_buff[0] == 0xC1:
        #             print(bytearray(r_buff))
        #             pass
        #         else:
        #             print(f"Unexpected response encountered during lora configuration:{r_buff}")
        #         break
        #     else:
        #         print("Missing response during lora configuration, trying again")
        #         pass
        
        self.ser.reset_input_buffer() # clear the input buffer
        self.ser.reset_output_buffer() # clear the output buffer

        GPIO.output(self.M0,GPIO.LOW)
        GPIO.output(self.M1,GPIO.LOW)
        time.sleep(0.1)

    def get_config(self):
        # the pin M1 of lora HAT must be high when enter setting mode and get parameters
        GPIO.output(self.M0, GPIO.LOW)
        GPIO.output(self.M1, GPIO.HIGH)
        time.sleep(0.1)
        self.ser.close()
        self.ser = serial.Serial(self.serial_n,self.SX126X_CONF_UART_BAUDRATE, timeout=self.timeout)
        # send command to get setting parameters
        self.ser.flushInput()
        time.sleep(0.1)

        self.ser.write(bytes([0xC1,0x00,0x09]))

        # start_time = time.time()
        # delta_time = time.time() - start_time

        while self.ser.inWaiting() < 9:
            # delta_time = time.time() - start_time
            # print(f"Aux pin: {GPIO.input(self.AUX)}") # This code makes my eyes hurt
            time.sleep(0.01)
        # print(delta_time)

        self.get_reg = self.ser.read(self.ser.inWaiting())
        
        
        # check the return characters from hat and print the setting parameters
        if self.get_reg[0] == 0xC1 and self.get_reg[2] == 0x09:
            addr_temp = (self.get_reg[3] << 8) + self.get_reg[4] 
            air_speed_temp = self.get_reg[6] & 0x07 
            power_temp = self.get_reg[7] & 0x03
            fre_temp = self.get_reg[8]
            
            print(f"Node address is {addr_temp}.")
            print(f"Air speed is {[key for key in self.lora_air_speed_dic if self.lora_air_speed_dic[key] == air_speed_temp]} bps")
            print(f"Power is {[key for key in self.lora_power_dic if self.lora_power_dic.get(key) == power_temp]} dBm")
            print(f"Frequency offset/channel: {850 + fre_temp}.125MHz.")
            # time.sleep(0.5)

        self.ser.close()
        self.ser = serial.Serial(self.serial_n,self.baudrate, timeout=self.timeout)
        GPIO.output(self.M1,GPIO.LOW)
        return self.get_reg[3::]

    def get_device_model(self):
        '''
        Get model of device (e.g. b"E22-900T22S")

        returns device model saved from startup, reads device model using AT command when in configuration mode
        '''
        return b"E22-900T22S"
        # if GPIO.input(self.M0) != GPIO.LOW or GPIO.input(self.M1) != GPIO.HIGH:
        #     return self.device_model
        # self.ser.reset_input_buffer()
        # self.ser.write(b"AT+DEVTYPE=?")
        # # time.sleep(1) # hardcoded might be bad here idk
        # device_model = b""
        # while b"\n\00" not in device_model:
        #     device_model += self.ser.read()
        #     time.sleep(0.1)
        # return device_model[8:19]
    
    def send(self,data:bytes|bytearray):
        """
        Send uses the first two bytes as destination address, one byte for net_id (frequency)

        DO NOT INCLUDE ADDRESS AND NETID IF USING TRANSPARENT MODE 
        [address low] [address high] [net_id] [content length] 

        The sender's address and net_id should be included as content

        [sender address low] [ sender address high] [ sender net_id ]
        """
        # print(f"M1 : {GPIO.input(self.M1)}")
        # print(f"AUX pre : {GPIO.input(self.AUX)}")
        
        while self.ser.out_waiting > 0 or GPIO.input(self.AUX) == 0:
            time.sleep(0.001)
        
        # print(f"AUX post: {GPIO.input(self.AUX)}")

        self.ser.write(data)

        # THIS SECTION WAITS FOR AUX TO REACT
        if self.debug: st = time.perf_counter()
        while GPIO.input(self.AUX) == 1:# TODO: might be good with a timeout here
            # time.sleep(0.0001) # Alternative to busy wait
            pass
        if self.debug:
            et = time.perf_counter()
            print(f"DEBUG: time until aux reacted: {et - st}")

        # # TODO: TEST IF THIS IS NEEDED, REMOVING IT COULD INCREASE SINGLE MESSAGE PERFORMANCE (wait until aux has reacted, then wait until aux is ready)
        # while self.ser.out_waiting > 0 or GPIO.input(self.AUX) == 0:
        #     time.sleep(0.001)


        # if self.debug: 
        #     msg_transmit_time = time.perf_counter() - et
        #     print(f"DEBUG: total aux working time: {msg_transmit_time}")

        # Should RSSI be here? 
        if self.rssi == True:
            self.get_channel_rssi() 
        
    def receive(self):
        """
        ### non-blocking receive

        ### Returns 
        None: object when no packet inbound.\n        
        bytes: object when packet inbound.\n
        
        bytes, or tuple (bytes, rssi) when rssi is enabled
        
        Function assumes first byte is length of message
        """
        if self.ser.inWaiting() > 1: 
            # wait for length header, and first content byte 
            
            r_buff = self.ser.read()
            # 1st byte contains tot. number of bytes in packet
            packet_size = r_buff[0]
            # TODO: ADD DETECTION OF BROKEN PACKETS, THEY SHOULD BE DROPPED (like udp) (firmware does this, but it doesn't guarantee buffer overflows after and before reception)
            # TODO: Test this with packets larger than single packet sizes
            # TODO: Make this work when using mode that doesn't include sender ip in header 
            if self.debug: print(f"DEBUG: r_buff: {r_buff}")
            if self.debug: print(f"DEBUG: Reading {packet_size} bytes")
            
            # ! THIS SECTION LOOPS INDEFINETLY IF PACKET SIZE HEADER IS CORRUPTED (and the input is not cleared without reconfig)
            while True: 
                r_buff += self.ser.read() 
                # if self.debug: print(f"DEBUG: r_buff: {r_buff}\r", end='')
                if len(r_buff) >= packet_size: 
                    #self.ser.inWaiting()  # This line does nothing? 
                    break
            # if self.debug: print()
            msg = r_buff
            
            # print the rssi
            if self.rssi:

                # Read rssi packet signal strength/clarity byte 
                r_buff += self.ser.read()  

                print("the packet rssi value: -{0}dBm".format(256-r_buff[-1:][0]))
                # self.get_channel_rssi()
                return (msg, (256-r_buff[-1:][0]))
            else:
                return msg
            
    def receive_time(self, listen_time):
        """
        ### Read incoming buffer for set time

        ### Returns 
        None: object when no packet inbound.\n        
        bytes: object when packet inbound.\n
        
        tuple (bytes, rssi) if rssi is enabled
        """
        # This receive does not use the message length header field, instead it reads the buffer for a set period.
        if self.ser.inWaiting() > 0: 
            r_buff = b""
            starttime = time.time()
            deltatime = time.time()
            while deltatime - starttime < listen_time: 
                deltatime = time.time()
                r_buff += self.ser.read_all() 

            msg = r_buff
            # print(f"msg: {msg}")
            return msg
        

    def get_channel_rssi(self):
        """
        Give RSSI signal noise readout

        TODO: make function work for other uart baudrates than 9600 (Switch to 9600, then reverse to previous rate)
        """
        GPIO.output(self.M1,GPIO.LOW)
        GPIO.output(self.M0,GPIO.LOW)
        while GPIO.input(4) == 0:
            pass
        self.ser.flushInput()
        self.ser.write(bytes([0xC0,0xC1,0xC2,0xC3,0x00,0x02])) 
        time.sleep(0.5)
        re_temp = bytes(5)
        if self.ser.inWaiting() > 0:
            time.sleep(0.1)
            re_temp = self.ser.read(self.ser.inWaiting())
        if re_temp[0] == 0xC1 and re_temp[1] == 0x00 and re_temp[2] == 0x02:
            print("the current noise rssi value: -{0}dBm".format(256-re_temp[3]))
            # print("the last receive packet rssi value: -{0}dBm".format(256-re_temp[4]))
        else:
            # pass
            print("receive rssi value fail")
            # print("receive rssi value fail: ",re_temp)

    def sleep(self):
        GPIO.output(self.M1, GPIO.HIGH)
        GPIO.output(self.M0, GPIO.HIGH)
        time.sleep(0.1)

    def wake(self):
        GPIO.output(self.M1, GPIO.LOW)
        GPIO.output(self.M0, GPIO.LOW)
        time.sleep(0.1)