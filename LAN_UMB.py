#!/usr/bin/python3

import time
import struct
import socket

class UMBError(BaseException):
    pass

class LAN_UMB:
    """
    This is a simple driver for communicating to Weatherstations
    made by the German company Lufft. It implements their UMB-Protocol.
    You just need a USB-to-RS485 dongle and connect it to your PWS 
    according to the wiring diagram you find in the manual.
    Downsides: This class does not replace the UMB-config-tool, because
    its not able to set the config values in your PWS at the moment.
    
    Attributes
    ----------
    ip : string
        IP address. Default is 10.0.1.26
    
    port : integer
        The default port number is 52015
        
    Methods
    -------
    onlineDataQuery (channel, receiver_id=1):
        Use this method to request a value from one channel.
        It will return a (value, status) tuple.
        Status number 0 means everything is ok.
        It have more the one PWS on the BUS, use receiver_id to
        distinguish between them.
        
    send_request(receiver_id, command, version, payload)
        Send a command to the weather station
    
    checkStatus(status):
        You can lookup, what a status number means.
    
    Usage
    -----
    1. In your python-script: 
        from LAN_UMB import LAN_UMB
        
        with LAN_UMB(ip=<address of the device>) as umb:
            value = umb.onlineDataQuery(<channel number>)
            print(value)
    
    2. As a standalone program:
        ./LAN_UMB.py 100 111 200 300 460 580
    """

    def __init__(self, ip, port=52015):
        self.ip = ip
        self.port = port
    
    def __enter__(self): # throws a SerialException if it cannot connect to device
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect((self.ip, self.port))

        return self
    
    def __exit__(self, exception_type, exception_value, traceback):
        self.s.close()
            
    # The devices do not send <CR><LF>, thus the receive command
    # will only return after timeout. In order to cope with longer
    # delays up the 10 receive commands are issued as long as there
    # data.
    def readFromLAN(self, timeout=0.1):
        self.s.settimeout(timeout)
        data = b''
        
        loops = 0
        while loops < 10:
            try:
                new_data = self.s.recv(1024)
                data = data + new_data
            except socket.timeout:
                if len(data) < 12:
                    loops = loops +1
                else:
                    loops = 1000
                
        return data
    
    def calc_next_crc_byte(self, crc_buff, nextbyte):
        for i in range (8):
            if( (crc_buff & 0x0001) ^ (nextbyte & 0x01) ):
                x16 = 0x8408;
            else:
                x16 = 0x0000;
            crc_buff = crc_buff >> 1;
            crc_buff ^= x16;
            nextbyte = nextbyte >> 1;
        return(crc_buff);
    
    def calc_crc16(self, data):
        crc = 0xFFFF;
        for byte in data:
            crc = self.calc_next_crc_byte(crc, byte);
        return crc
    
    # Handle communication with the device
    # Returns payload of the answer; use the specific functions
    # `parse_<cmd>` to interprete the response
    def send_request(self, receiver_id, command, command_version, payload=''):
        
        SOH, STX, ETX, EOT= b'\x01', b'\x02', b'\x03', b'\x04'
        VERSION = b'\x10'
        TO = int(receiver_id).to_bytes(1,'little')
        TO_CLASS = b'\x70'
        FROM = int(1).to_bytes(1,'little')
        FROM_CLASS = b'\xF0'
        
        LEN = 2
        for payload_byte in payload:
            LEN += 1
        LEN = int(LEN).to_bytes(1,'little')
        
        
        COMMAND = int(command).to_bytes(1,'little')
        COMMAND_VERSION = int(command_version).to_bytes(1,'little')
        
        # Assemble transmit-frame
        if len(payload) > 0:
            tx_frame = SOH + VERSION + TO + TO_CLASS + FROM + FROM_CLASS + LEN + STX + COMMAND + COMMAND_VERSION + payload + ETX
        else:
            tx_frame = SOH + VERSION + TO + TO_CLASS + FROM + FROM_CLASS + LEN + STX + COMMAND + COMMAND_VERSION + ETX

        # calculate checksum for transmit-frame and concatenate
        tx_frame += self.calc_crc16(tx_frame).to_bytes(2, 'little') + EOT
        
        # Write transmit-frame to serial
        self.s.send(tx_frame)
        #print([hex(c) for c in tx_frame])
        
        ### < --- --- > ###
        
        # Read frame from serial
        rx_frame = self.readFromLAN()
        #print([hex(c) for c in rx_frame])
        
        if len(rx_frame) == 0:
            print("Nothing received - try again")
            return(0)
        
        # Check the length of the frame
        length = int.from_bytes(rx_frame[6:7], byteorder='little')
        if (rx_frame[8+length:9+length] != ETX):
            raise UMBError("RX-Error! Length of Payload is not valid. length-field says: " + str(length))
            
        # Drop data that has arievd too late
        if (len(rx_frame) > length + 12):
            print("Drop old data")
            rx_frame = rx_frame[length+12:]
     
        # compare checksum field to calculated checksum
        cs_calculated = self.calc_crc16(rx_frame[:-3]).to_bytes(2, 'little')
        cs_received = rx_frame[-3:-1]
        if (cs_calculated != cs_received):
            raise UMBError("RX-Error! Checksum test failed. Calculated Checksum: " + str(cs_calculated) + "| Received Checksum: " + str(cs_received))
     
        # Check if all frame field are valid
        if (rx_frame[0:1] != SOH):
            raise UMBError("RX-Error! No Start-of-frame Character")
        if (rx_frame[1:2] != VERSION):
            raise UMBError("RX-Error! Wrong Version Number")
        #if (rx_frame[2:4] != (FROM + FROM_CLASS)):
        #    raise UMBError("RX-Error! Wrong Destination ID")
        #if (rx_frame[4:6] != (TO + TO_CLASS)):
        #    raise UMBError("RX-Error! Wrong Source ID")
        if (rx_frame[7:8] != STX):
            raise UMBError("RX-Error! Missing STX field")
        if (rx_frame[8:9] != COMMAND):
            raise UMBError("RX-Error! Wrong Command Number")
        if (rx_frame[9:10] != COMMAND_VERSION):
            raise UMBError("RX-Error! Wrong Command Version Number")
         
        #
        # Todo: The pay load needs to be handled depending on the command
        #
        payload = rx_frame[10:8+length]
        return(payload)

    # Commands to parse 

    # cmd 0x23 and 0x2F
    def parse_data_request(self, payload):
                
        type_of_value = int.from_bytes(payload[3:4], byteorder='little')
        value = 0
        
        if type_of_value == 16:     # UNSIGNED_CHAR
            value = struct.unpack('<B', payload[4:5])[0]
        elif type_of_value == 17:   # SIGNED_CHAR
            value = struct.unpack('<b', payload[4:5])[0]
        elif type_of_value == 18:   # UNSIGNED_SHORT
            value = struct.unpack('<H', payload[4:6])[0]
        elif type_of_value == 19:   # SIGNED_SHORT
            value = struct.unpack('<h', payload[4:6])[0]
        elif type_of_value == 20:   # UNSIGNED_LONG
            value = struct.unpack('<L', payload[4:8])[0]
        elif type_of_value == 21:   # SIGNED_LONG
            value = struct.unpack('<l', payload[4:8])[0]
        elif type_of_value == 22:   # FLOAT
            value = struct.unpack('<f', payload[4:8])[0]
        elif type_of_value == 23:   # DOUBLE
            value = struct.unpack('<d', payload[4:12])[0]
        
        return (value)
    
    # cmd 0x2F
    def parse_multi_channel_request(self, payload):
    
        n = int.from_bytes(payload[1:2], byteorder='little')
        #print("Number of values %d" % n)
        
        ptr = 2
        valist = []
        for i in range(0,n):
            nsub = int.from_bytes(payload[ptr:ptr+1], byteorder='little')
            #print("Sub length %d" % nsub)
            
            value = self.parse_data_request(payload[ptr+1:ptr+nsub+2])
            valist.append(value)
            ptr = ptr + nsub + 1
        
        return (valist)

    # cmd 0x26
    def parse_status_request(self, payload):

        status = int.from_bytes(payload[1:2], byteorder='little')
        return(status)

    def checkStatus(self, status):
        #
        # Todo: add the calling function here
        #
    
        if status == 0:
            return ("Command successful; no error; all OK")
        elif status == 16:
            return ("Unknown command; not supported by this device")
        elif status == 17:
            return ("Status: ungültige Parameter")
        elif status == 18:
            return ("Invalid parameter")
        elif status == 19:
            return ("Invalid version of the command")
        elif status == 20:
            return ("Invalid password for command")
        elif status == 32:
            return ("Read error")
        elif status == 33:
            return ("Write error")
        elif status == 34:
            return ("Length too great; max. permissible length is designated in <maxlength>")
        elif status == 35:
            return ("Invalid address / storage location")
        elif status == 36:
            return ("Invalid channel")
        elif status == 37:
            return ("Command not possible in this mode")
        elif status == 38:
            return ("Unknown calibration command")
        elif status == 39:
            return ("Calibration error")
        elif status == 40:
            return ("Device not ready; e.g. initialisation / calibration running")
        elif status == 41:
            return ("Undervoltage")
        elif status == 42:
            return ("Hardware error")
        elif status == 43:
            return ("Measurement error")
        elif status == 44:
            return ("Error on device initialization")
        elif status == 45:
            return ("Error in operating system")
        elif status == 48:
            return ("Configuration error, default configuration was loaded")
        elif status == 49:
            return ("Calibration error / the calibration is invalid, measurement not possible")
        elif status == 50:
            return ("CRC error on loading configuration; default configuration was loaded")
        elif status == 51:
            return ("CRC error on loading calibration; measurement not possible")
        elif status == 52:
            return ("Calibration step 1")
        elif status == 53:
            return ("Calibrations OK")
        elif status == 54:
            return ("Channel deactivated")
  
    # cmd 0x28
    def parse_readout_time_request(self, payload):

        ts = int.from_bytes(payload[1:4], byteorder='little')
        return(ts)

    # cmd 0x2D
    def parse_device_info(self, payload):

        # The OPUS device seem to always return 0x10
        # May be device information is not supported?!
        print(payload)
        return(0)


    def onlineDataQuery(self, channel, receiver_id=1):
        
        value = 0
        payload = self.send_request(receiver_id, 0x23, 0x10, int(channel).to_bytes(2,'little'))
        if (payload != 0):
            value = self.parse_data_request(payload)
        return(value)
    
    def onlineMultiChannelQuery(self, chlist, receiver_id=1):
        
        chbyteseq = len(chlist).to_bytes(1,'little')
        for channel in chlist:
            chbyteseq = chbyteseq + int(channel).to_bytes(2,'little')
        
        valist = []
        payload = self.send_request(receiver_id, 0x2F, 0x10, chbyteseq)
        if (payload != 0):
            valist = self.parse_multi_channel_request(payload)
        return (valist)

    def statusQuery(self, receiver_id=1):
    
        status = -1
        payload = self.send_request(receiver_id, 0x26, 0x10)
        if (payload != 0):
            status = self.parse_status_request(payload)
        return(status)

    def readoutTimeQuery(self, receiver_id=1):
        
        ts = 0
        payload = self.send_request(receiver_id, 0x28, 0x10)
        if (payload != 0):
            ts = self.parse_readout_time_request(payload)
        return(ts)
        
    def deviceInfoQuery(self, receiver_id=1):
        
        info = b''
        # Device identification
        #payload = self.send_request(receiver_id, 0x2D, 0x10, b'\x10')
        # Device description
        #payload = self.send_request(receiver_id, 0x2D, 0x10, b'\x11')
        # Hardware and software version
        #payload = self.send_request(receiver_id, 0x2D, 0x10, b'\x12')
        # Number of channels
        payload = self.send_request(receiver_id, 0x2D, 0x10, b'\x15')
        if (payload != 0):
            info = self.parse_device_info(payload)
        return(info)



#
# Sample usage of the UMS class
#

import sys
import json
from datetime import datetime
import argparse


if __name__ == "__main__":

    # Define command line options
    parser = argparse.ArgumentParser()
    parser.add_argument('--ip', help='IP address of the device', default = '10.0.1.26')
    parser.add_argument('--loop', help='read data in a loop', action='store_true')
    parser.add_argument('channels', nargs='+', help='list of channels to be read')
    args = parser.parse_args()


    # Query a list of channels (max 20)
    chlist = []
    for channel in args.channels:
        if 100 <= int(channel) <= 29999:
            chlist.append(channel)

    # 1. Single call, return JSON list of sensor id and their values
    if args.loop == False:

        with LAN_UMB(ip=args.ip) as umb:
            valist = umb.onlineMultiChannelQuery(chlist)

            mydict = {}
            for channel,value in zip(chlist,valist):
                mydict[channel] = value
            print (datetime.now(), json.dumps(mydict, separators=(',', ': ')))
 
            # Query device info
            #umb.deviceInfoQuery()
 
            # Query single channels
            #for channel in sys.argv[1:]:
            #    if 100 <= int(channel) <= 29999:
            #        value = umb.onlineDataQuery(channel)
            #        mydict[channel] = value
         
            # Readout time
            #ts = umb.readoutTimeQuery()
            #print("Readout time %d" % ts)

            # Query status
            #status = umb.statusQuery()
            #print("Status %s" % umb.checkStatus(status))

         
    # 2. Continuous loop, with display, when data changes
    if args.loop == True:

        with LAN_UMB(ip=args.ip) as umb:

            lastvalues = [0] * len(chlist)
            while(args.loop):
                mydict = {}

                # Read data
                valist = umb.onlineMultiChannelQuery(chlist)
                for channel,value in zip(chlist,valist):
                    mydict[channel] = value

                # print values only, if they have changed
                changed = 0
                if len(valist) > 0:
                    for last, value in zip(lastvalues, valist):
                        if last != value:
                            changed = changed + 1
                if changed > 0:
                    print(datetime.now(), changed, valist)
                    lastvalues = valist
                    
                time.sleep(1)

