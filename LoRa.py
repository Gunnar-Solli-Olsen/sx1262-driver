import sx126x
import time
import hashlib

class LoRa:
    #
    # Default values for LoRa    
    # SERIAL PORT IS RPi SPECIFIC
    #
    
    def __init__(self, FREQ = 868, CHANNEL = 65535, SERIAL_PORT="/dev/serial0", power=22, uart_baudrate=9600, air_speed=2400, timeout:float|None=None, info:bool=False, debug:bool=False, warning:bool=True):
        self.freq = FREQ
        self.channel = CHANNEL
        self.serial_port = SERIAL_PORT
        self.timeout = timeout
        self.info = info
        self.debug = debug
        self.warning = warning
        self.power = power
        self.uart_baudrate = uart_baudrate
        self.air_speed = air_speed
        self.lora_node = self.setup_sx1262(self.serial_port, self.freq, self.channel, self.power, rssi=False, uart_baudrate=self.uart_baudrate, air_speed=self.air_speed, timeout=timeout) 
        self.SX126X_UART_BAUDRATE = self.lora_node.SX126X_UART_BAUDRATE

    def setup_sx1262(self, serial_num, freq, addr,power=22,rssi=False,prev_uart_baudrate=None, uart_baudrate=9600, air_speed=2400,relay=False,timeout:float|None=None):
        return sx126x.sx126x(serial_num,freq, addr, power, rssi, prev_uart_baudrate, uart_baudrate, air_speed, relay, timeout=timeout)
    
    def change_settings(self, FREQ = None, CHANNEL = None, SERIAL_PORT=None, power:int|None=None, uart_baudrate=None, air_speed:int|None=None, timeout:float|None=None):
        # if new value, set value to new value 
        print("changing settings...")
        if FREQ: self.freq = FREQ
        if CHANNEL: self.channel = CHANNEL
        if SERIAL_PORT: self.serial_port = SERIAL_PORT
        if power: self.power = power
        old_baud_rate = None 
        if uart_baudrate: 
            self.uart_baudrate = uart_baudrate
            old_baud_rate = self.lora_node.ser.baudrate
            if self.debug: print("DEBUG: previous baudrate:", old_baud_rate)
        if air_speed: self.air_speed = air_speed
        if timeout: self.timeout = timeout
        
        self.lora_node = self.setup_sx1262(self.serial_port, self.freq, self.channel, rssi=False, power=self.power, prev_uart_baudrate=old_baud_rate, uart_baudrate=self.uart_baudrate, air_speed=self.air_speed, timeout=self.timeout) 

        time.sleep(0.5)

    def checksum(self, data:bytes|bytearray):
        """
        Generate checksum from data using sha-256
        """
        checksum_generator = hashlib.sha256()
        checksum_generator.update(bytes(data))
        result = checksum_generator.digest()
        return result

    def pack_packet(self, destination:int, sender:int, content:bytes|bytearray):
        """
        creates bytes object that includes destination, sender, length of packet, and content in packet.
        """
        address_dest = destination.to_bytes(2)
        address_sender = sender.to_bytes(2)
        # TODO: figure out what 18 and 12 mean in this context (dogmaticly adding them currently)
        packet_size = (7+len(content)).to_bytes()

        packet = address_dest + bytes([18]) + address_sender + bytes([12]) + packet_size + bytes(content)
        return packet

    
    # 
    # 
    # TODO: check that data can actually be both bytes and bytearrays 
    #
    def send(self, address:int, data:bytearray|bytes):
        """
        Transmit data to lora device with address.
        This transmission does not guarantee that the packages are received.

        Parameters:
            address (2 byte integer): Address of destination device
            data (bytearray or bytes): Data to be transmitted. 
        """

        if address.bit_length() > 16:
            raise Exception("INVALID ADDRESS LENGTH")
        
        print("Incoming data type: ", type(data))
        if len(data) > 233 and self.info:
            print("INFO: data does not fit in a single LoRa message")
    
        max_msg_size = 233
        segmented_data = [data[i:i+max_msg_size] for i in range(0, len(data), max_msg_size) ]
        
        try: # This test is not necessary
            for d in segmented_data: 
                bytes(d)
        except:
            print("##################\nFailed to turn data to bytes, please provide valid __bytes__ override for the input data!\n##################")
            print("Failed to convert the following to bytes: ", d)
            print("Failed bytes conversion comes from this: ", segmented_data)
            raise

        data_length = len(data)
        print("Datalength: ", data_length)

        checksum = self.checksum(data)
        if self.debug: print("DEBUG: Checksum, sender:", checksum)

        print("Segments: ", len(segmented_data))
                                                      #    In practice this byte will never exceed 255
                                                      #       |vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv|
        encoded_data = self.pack_packet(address, self.channel, bytes(len(segmented_data).to_bytes()) + bytes(checksum))
        if self.debug: print("DEBUG: sending metadata :",encoded_data)
        
        self.lora_node.send(encoded_data)
        time.sleep(0.1)
        i = 0
        for d in segmented_data:
            i+=1
            print("sending packet", i, "of", len(segmented_data))
            encoded_data = self.pack_packet(address, self.channel, bytes(d))
            print("Encoded data length:", len(encoded_data))
            print("included data size:", encoded_data[6])
            if self.debug: print("DEBUG: sending:", encoded_data)
            self.lora_node.send(encoded_data)
            
        # Check if receiver reached same checksum
        starttime = time.time()

        while True: # TODO: Change these to return codes
            delta = (time.time() - starttime)
            rec = self.lora_node.receive()
            if rec:
                if checksum == rec[4::]:
                    print("Correct checksum received")
                    return 0
                else:
                    print("Checksum failure on send! \ntarget: ", checksum, "\nactual: ", rec[4::])
                    return 1
            elif self.timeout:
                if delta > self.timeout:
                    print("Timeout surpassed!")
                    return 2

    def receive(self):
        ret = self.lora_node.receive()
        if ret:
            sender_address = int.from_bytes(ret[0:2])
            if self.debug: print("DEBUG: Received packet from sender:", sender_address)
            if self.debug: print("DEBUG: content:", ret)
            tot_packets = int(ret[4])
            target_checksum = (ret[5::])
            print("Total incoming packets: ", tot_packets)
            incoming_data = bytes()
            for i in range(tot_packets):
                
                received = False
                packet = None
                while not received: # This should be changed to a until a timer runs out
                    packet = self.lora_node.receive()
                    if packet:
                        received = True
                        incoming_data += bytearray(packet[4::])
                    # time.sleep(0.1)

                if self.info: print("INFO: Received packet ", i+1, " of ", tot_packets)
            if self.info: print("INFO: Received all packets, verifying checksum")

            checksum = self.checksum(incoming_data)
            if checksum == target_checksum:
                if self.debug: print("DEBUG: successfully verified checksum!")
                ret_packet = self.pack_packet(sender_address, self.channel, bytes(checksum))
                self.lora_node.send(ret_packet)
                if self.debug: print("DEBUG: ", ret_packet)
                return incoming_data
            else:
                if self.debug: print("DEBUG: Checksum failure on receive! \ntarget: ", target_checksum, "\nactual: ", checksum)
                self.lora_node.send(self.pack_packet(sender_address, self.channel, bytes(checksum)))

    # TODO: Add feature to select message size
    def raw_send(self, address, data:bytes|bytearray):

        if address.bit_length() > 16:
            raise Exception("INVALID ADDRESS LENGTH")
        if len(data) > 233 and self.warning:
            print("WARNING: data does not fit in a single LoRa message")

        packet = self.pack_packet(address, self.channel, bytes(len(data).to_bytes()) + bytes(data))
        if self.debug: print("Packet: ", packet)
        self.lora_node.send(packet)

    def raw_recv(self):
        ret = self.lora_node.receive()
        if ret:
            if self.debug: print("DEBUG: Reading incoming packet")
            return ret
            # incoming_data = bytes()
            # received = False
            # packet = None
            # while not received: # This should be changed to add a 
            #     packet = self.lora_node.receive()
            #     if packet:
            #         received = True
            #         incoming_data += bytearray(packet[4::])
            #     time.sleep(0.1)
            # return incoming_data

    def sleep(self):
        """
        Set LoRa device mode to 'Deep sleep'

        This will disable sending and receiving transmissions
        """
        self.lora_node.sleep()

    def wake(self):
        """
        Set LoRa device mode to 'transmission'

        This enables sending and receiving transmissions
        """
        self.lora_node.wake()