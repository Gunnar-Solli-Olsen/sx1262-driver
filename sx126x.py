# This file is used for LoRa and Raspberry pi4B related issues 

import RPi.GPIO as GPIO
import serial
import time

class sx126x:

    M0 = 22
    M1 = 27
    # if the header is 0xC0, then the LoRa register settings dont lost when it poweroff, and 0xC2 will be lost. 
    cfg_reg = [0xC0,0x00,0x09,0x00,0x00,0x00,0x62,0x00,0x17,0x43,0x00,0x00]
    # cfg_reg = [0xC2,0x00,0x09,0x00,0x00,0x00,0x62,0x00,0x12,0x43,0x00,0x00]
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
    start_freq = 850

    #
    # offset between start and end frequence of two lora module
    #
    # E22-400T22S           E22-900T22S
    # 410~493MHz      or    850~930MHz
    offset_freq = 18

    # power = 22
    # air_speed = 2400

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
        300:0x00, 
        1200:0x01,
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

    lora_buffer_size_dic = {
        240:SX126X_PACKAGE_SIZE_240_BYTE,
        128:SX126X_PACKAGE_SIZE_128_BYTE,
        64:SX126X_PACKAGE_SIZE_64_BYTE,
        32:SX126X_PACKAGE_SIZE_32_BYTE
    }

    def __init__(self,serial_num,freq,addr,power,rssi,prev_baud_rate:int|None=None, uart_baudrate=9600,air_speed=2400,\
                 net_id=0,buffer_size = 240,crypt=0,\
                 relay=False,lbt=False,wor=False, timeout:float|None=None):
        """
        Params:
            serial_num (string): Serial port number (default "/dev/ttyS0" for RPi w. debian)
            freq (int): Frequency to use for transmission, 433 and 868 MHz are usable in the EU 
            addr (int): 2 byte address to use for device, incoming messages will be received with this address, and outgoing messages will include this address.    
            power (int): transmission power in decibel, choose from these values [10, 13, 17, 22]    
            rssi (bool): Include signal noise information
            uart_baudrate (int): uart baud rate for transmissions, starts at 9600 as default. Note that this rate only applies to communication, not for configuration
            air_speed (int): air speed of transmissions, should be identical between sender and receiver
            net_id (int): network id, MUST BE IDENTICAL BETWEEN SENDER AND RECEIVER
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
        # Initial the GPIO for M0 and M1 Pin
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.M0,GPIO.OUT)
        GPIO.setup(self.M1,GPIO.OUT)
        GPIO.output(self.M0,GPIO.LOW)
        GPIO.output(self.M1,GPIO.HIGH)

        self.conf_baudrate = 9600 

        # The hardware UART of Pi3B+,Pi4B is /dev/ttyS0 (or you can map it to another one manually lol)
        self.ser = serial.Serial(serial_num,self.conf_baudrate, timeout=self.timeout)
        self.ser.flushInput()

        self.set(freq,addr,power,rssi,uart_baudrate,air_speed,net_id,buffer_size,crypt,relay,lbt,wor)

        self.ser.close()
        self.ser = serial.Serial(serial_num,uart_baudrate, timeout=self.timeout)
 

    def set(self,freq,addr,power,rssi,uart_baudrate=9600,air_speed=2400,\
            net_id=0,buffer_size = 240,crypt=0,\
            relay=False,lbt=False,wor=False):
        self.addr = addr
        # We should pull up the M1 pin when sets the module
        GPIO.output(self.M0,GPIO.LOW)
        GPIO.output(self.M1,GPIO.HIGH)
        time.sleep(0.1) # This annoys me but it is necessary

        low_addr = addr & 0xff
        high_addr = addr >> 8 & 0xff
        net_id_temp = net_id & 0xff
        if freq > 850:
            freq_temp = freq - 850
            self.start_freq = 850
            self.offset_freq = freq_temp
        elif freq > 410:
            freq_temp = freq - 410
            self.start_freq  = 410
            self.offset_freq = freq_temp
        
        air_speed_temp = self.lora_air_speed_dic.get(air_speed,None)
        # if not air_speed_temp is None:
        #     raise Exception("stop right there criminal scum, set airspeed to a value or serve your sentence, we couldn't find a value corresponding to", air_speed)
        
        buffer_size_temp = self.lora_buffer_size_dic.get(buffer_size,None)
        # if air_speed_temp != None:
        
        power_temp = self.lora_power_dic.get(power,None)
        #if power_temp != None:

        if rssi:
            # enable print rssi value 
            rssi_temp = 0x80
        else:
            # disable print rssi value
            rssi_temp = 0x00        

        # get crypt
        l_crypt = crypt & 0xff
        h_crypt = crypt >> 8 & 0xff
        
        if relay==False:
            self.cfg_reg[3] = high_addr
            self.cfg_reg[4] = low_addr
            self.cfg_reg[5] = net_id_temp
            self.cfg_reg[6] = self.SX126X_UART_BAUDRATE[uart_baudrate] + air_speed_temp
            print((self.SX126X_UART_BAUDRATE[uart_baudrate] + air_speed_temp).to_bytes(1))
            # 
            # it will enable to read noise rssi value when add 0x20 as follow
            # 
            self.cfg_reg[7] = buffer_size_temp + power_temp + 0x20
            self.cfg_reg[8] = freq_temp
            #
            # it will output a packet rssi value following received message
            # when enable eighth bit with 06H register(rssi_temp = 0x80)
            #
            self.cfg_reg[9] = 0x43 + rssi_temp
            self.cfg_reg[10] = h_crypt
            self.cfg_reg[11] = l_crypt
        else:
            self.cfg_reg[3] = 0x01
            self.cfg_reg[4] = 0x02
            self.cfg_reg[5] = 0x03
            self.cfg_reg[6] = self.SX126X_UART_BAUDRATE[uart_baudrate] + air_speed_temp
            # 
            # it will enable to read noise rssi value when add 0x20 as follow
            # 
            self.cfg_reg[7] = buffer_size_temp + power_temp + 0x20
            self.cfg_reg[8] = freq_temp
            #
            # it will output a packet rssi value following received message
            # when enable eighth bit with 06H register(rssi_temp = 0x80)
            #
            self.cfg_reg[9] = 0x03 + rssi_temp
            self.cfg_reg[10] = h_crypt
            self.cfg_reg[11] = l_crypt


        for i in range(3):
            written = self.ser.write(bytes(self.cfg_reg)) # write config to registers
            while self.ser.out_waiting > 0:
                time.sleep(0.01)
            print("Written: ", written, "of", len(self.cfg_reg))

            # Wait longer during retries, this lowers the configuration time for higher baud-rates
            time.sleep(1+i*2) # wait for 1, 3, 5 seconds when applying settings

            if self.ser.inWaiting() > 0:
                time.sleep(0.5)
                r_buff = self.ser.read(self.ser.inWaiting()) # Read answer from buffer
                if r_buff[0] == 0xC1:
                    pass
                else:
                    print(f"Unexpected response encountered during lora configuration:{r_buff}")
                break
            else:
                print("Missing response during lora configuration, trying again")
                pass
        

        # TODO: Consider removing this section, it fetches settings without doing anything with the settings
        self.ser.write(bytes([0xC1,0x00,0x09]))

        timeout = 5
        starttime = time.time()
        deltatime = 0

        while self.ser.in_waiting < 1:
            print( f'\r{self.ser.in_waiting}', end="", flush=True)
            deltatime = time.time() - starttime
            time.sleep(0.01)
            if deltatime > timeout:
                print("\nWARNING: TIMED OUT", end="")
                break
            print()
            print(f"waited {deltatime} seconds to change settings")

        self.ser.reset_input_buffer() # clear the input buffer
        self.ser.reset_output_buffer() # clear the output buffer

        GPIO.output(self.M0,GPIO.LOW)
        GPIO.output(self.M1,GPIO.LOW)
        time.sleep(0.1)

    def get_settings(self):
        # the pin M1 of lora HAT must be high when enter setting mode and get parameters
        #print(self.ser.baudrate)
        GPIO.output(self.M1,GPIO.HIGH)
        time.sleep(0.1)
        self.ser.close()
        self.ser = serial.Serial(self.serial_n,self.conf_baudrate, timeout=self.timeout)
        # send command to get setting parameters
        self.ser.flushInput()
        time.sleep(0.1)
        self.ser.write(bytes([0xC1,0x00,0x09]))
        time.sleep(0.5)
        if self.ser.inWaiting() > 9:
            time.sleep(0.5)
            self.get_reg = self.ser.read(self.ser.inWaiting())
        # check the return characters from hat and print the setting parameters
        if self.get_reg[0] == 0xC1 and self.get_reg[2] == 0x09:
            print(self.get_reg)
            fre_temp = self.get_reg[8]
            addr_temp = self.get_reg[3] + self.get_reg[4]
            air_speed_temp = self.get_reg[6] & 0x03
            power_temp = self.get_reg[7] & 0x03
            
            # print(f"Frequence is {fre_temp}.125MHz.")
            # print(f"Node address is {addr_temp}.")
            # print("Air speed is {0} bps"+ self.lora_air_speed_dic.get(None,air_speed_temp))
            # print("Power is {0} dBm" + self.lora_power_dic.get(None,power_temp))
            GPIO.output(self.M1,GPIO.LOW)
            time.sleep(0.5)
        self.ser.close()
        self.ser = serial.Serial(self.serial_n,self.baudrate, timeout=self.timeout)


    def send(self,data:bytes|bytearray):
        """
        the data format like as following "node address,frequence,payload" "20,868,Hello World\"
        """
        # Do we need this? 
        GPIO.output(self.M1,GPIO.LOW)
        GPIO.output(self.M0,GPIO.LOW)
        time.sleep(0.1)
        
        while self.ser.out_waiting > 0:
            time.sleep(0.01)
        
        self.ser.write(data)
        if self.rssi == True:
            self.get_channel_rssi()

        while self.ser.out_waiting > 0:
            time.sleep(0.01)
        
    def receive(self):
        """
        ### Non-blocking receive

        ### Returns 
        None: object when no packet inbound.\n        
        bytes: object when packet inbound.\n
        
        tuple (bytes, rssi) if rssi is enabled
        """
        if self.ser.inWaiting() > 4:
            # read first 4 bytes 
            
            r_buff = self.ser.read(4)
            # 4th byte contains tot. number of bytes in packet
            packet_size = r_buff[3]
            # ! THIS SECTION LOOPS INDEFINETLY IF PACKET SIZE HEADER IS CORRUPTED
            # TODO: ADD DETECTION OF THIS ERROR, BROKEN PACKETS SHOULD BE DROPPED (like udp)
            # TODO: doing this is made difficult due to the current timeout fault detection
            while True: 
                r_buff += self.ser.read() 
                if len(r_buff) == packet_size-3: 
                    self.ser.inWaiting() 
                    break

            msg = r_buff
            
            # print the rssi
            if self.rssi:

                # ! THIS CODE IS A GUESS AT BEST, DO NOT TRUST IT
                r_buff += self.ser.read()  
                # ! THIS CODE IS A GUESS AT BEST, DO NOT TRUST IT

                # TODO: Check if rssi still works
                print("the packet rssi value: -{0}dBm".format(256-r_buff[-1:][0]))
                # self.get_channel_rssi()
                return (msg, (256-r_buff[-1:][0]))
            else:
                return msg

    def get_channel_rssi(self):
        """
        Give RSSI signal noise readout

        TODO: make function work for other uart baudrates than 9600 (Switch to 9600, then reverse to previous rate)
        """
        GPIO.output(self.M1,GPIO.LOW)
        GPIO.output(self.M0,GPIO.LOW)
        time.sleep(0.1)
        self.ser.flushInput()
        self.ser.write(bytes([0xC0,0xC1,0xC2,0xC3,0x00,0x02])) # magic bytes
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