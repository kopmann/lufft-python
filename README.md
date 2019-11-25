# lufft-python

A Python API and driver for communication with weather stations made by the German company Lufft (e.g. OPUS20 family, WS600-UMB , ...) via LAN or serial port.
It implements the UMB protocol defined by Lufft. For the serial devices you will need a USB-to-RS485 dongle. The serial interface is currently handled by the separate implementation in `WS_UMB.py`. 

This class does not replace the Lufft configuration tools as it is not possible to modify the config via UMB protocol.

Links: 

- [UMB specification](https://www.lufft.com/download/manual-lufft-umb-protocol-en/)
- [User manual OPUS20 / BA - THI - THIP - THO](https://www.lufft.com/de-de/produkte/download-de/bedienanleitung-lufft-opus20-thi-thip-tco-de/)


## Usage

### In your python-script

The most relevant commands are implemented in the Python API:

- read a single value
- read multiple channels with a single call
- read status
- read device time (this is NOT the timestamp of any data)
- read device information (not working currently)

Example: Reading a single value

```python
from LAN_UMB import LAN_UMB

with LAN_UMB(ip = <ip address>) as umb:
    value = umb.onlineDataQuery(SomeChannelNumber)
    print(value)
```


### As a standalone python-program

Read values form the data logger.

```
# python LAN_UMB.py  -h
usage: LAN_UMB.py [-h] [--ip IP] [--loop] channels [channels ...]

positional arguments:
  channels    list of channels to be read

optional arguments:
  -h, --help  show this help message and exit
  --ip IP     IP address of the device
  --loop      read data in a loop

```


Example:

```shell
$ ./LAN_UMB.py --ip 10.0.1.26 100 111 200 300 460 580
```

