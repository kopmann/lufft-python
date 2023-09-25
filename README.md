# lufft-python

A Python API and driver for communication with weather stations made by the German company Lufft (e.g. OPUS20 family, WS600-UMB , ...) via LAN or serial port.
It implements the UMB protocol defined by Lufft. For the serial devices you will need a USB-to-RS485 dongle. The serial interface is currently handled by the separate implementation in `WS_UMB.py`. 

This class does not replace the Lufft configuration tools as it is not possible to modify the config via UMB protocol.

Links: 

- [UMB specification](https://www.lufft.com/download/manual-lufft-umb-protocol-en/)
- [UMB configuration tool](https://www.lufft.com/download/manual-lufft-umb-config-tool-en/)
- [User manual OPUS20 / BA - THI - THIP - THO](https://www.lufft.com/de-de/produkte/download-de/bedienanleitung-lufft-opus20-thi-thip-tco-de/)
- [OTT HydroMet Fellbach GmbH (before 2021 G. Lufft Mess- und Regeltechnik GmbH)](https://www.lufft.com/)


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
$ python LAN_UMB.py  -h
usage: LAN_UMB.py [-h] [--ip IP] [--loop] channels [channels ...]

positional arguments:
  channels    list of channels to be read

optional arguments:
  -h, --help  show this help message and exit
  --ip IP     IP address of the device
  --loop      read data in a loop

```


Examples: 

Read data

```shell
$ python LAN_UMB.py --ip 10.0.1.26 100 111 200 300 460 580
```

For the option `--loop` the data is read every second. Only when at least one of the requested values changes, the new dataset is plotted. The timestamp is generated on the PC side.

```shell
$ python LAN_UMB.py --ip 10.0.1.26 100 200 300 105 --loop
2019-11-25 18:17:47.682154 4 [22.034788131713867, 39.973628997802734, 995.6600341796875, 71.66261291503906]
2019-11-25 18:17:54.337096 1 [22.034788131713867, 39.973628997802734, 995.7000122070312, 71.66261291503906]
2019-11-25 18:18:04.314259 1 [22.034788131713867, 39.973628997802734, 995.6800537109375, 71.66261291503906]
2019-11-25 18:18:14.288812 2 [22.034788131713867, 39.98984909057617, 995.6900024414062, 71.66261291503906]
2019-11-25 18:18:24.266028 4 [22.031137466430664, 39.91762924194336, 995.6800537109375, 71.65605163574219]
2019-11-25 18:18:34.250189 1 [22.031137466430664, 40.09604263305664, 995.6800537109375, 71.65605163574219]
2019-11-25 18:18:44.221634 2 [22.031137466430664, 40.128482818603516, 995.6600341796875, 71.65605163574219]
2019-11-25 18:18:54.198888 2 [22.031137466430664, 40.11226272583008, 995.7100219726562, 71.65605163574219]
2019-11-25 18:19:04.192000 2 [22.031137466430664, 40.16094970703125, 995.7200317382812, 71.65605163574219]
2019-11-25 18:19:14.169253 2 [22.031137466430664, 40.079830169677734, 995.6800537109375, 71.65605163574219]
2019-11-25 18:19:24.150113 4 [22.042593002319336, 40.09730911254883, 995.7000122070312, 71.67666625976562]
2019-11-25 18:19:34.145555 1 [22.042593002319336, 40.09730911254883, 995.6700439453125, 71.67666625976562]
2019-11-25 18:19:44.129116 2 [22.042593002319336, 40.06486892700195, 995.7500610351562, 71.67666625976562]
2019-11-25 18:19:54.111483 2 [22.042593002319336, 40.03242111206055, 995.6500244140625, 71.67666625976562]
2019-11-25 18:20:04.093601 1 [22.042593002319336, 39.772987365722656, 995.6500244140625, 71.67666625976562]
2019-11-25 18:20:14.078807 2 [22.042593002319336, 40.000003814697266, 995.6800537109375, 71.67666625976562]
2019-11-25 18:20:24.067570 4 [22.038942337036133, 39.992671966552734, 995.6700439453125, 71.67008972167969]
```

