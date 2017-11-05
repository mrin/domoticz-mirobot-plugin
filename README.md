
# Xiaomi Mi Robot Vacuum - Domoticz Python plugin

*This plugin uses the [Python-miio](https://github.com/rytilahti/python-miio) library.*

*See this [link](https://www.domoticz.com/wiki/Using_Python_plugins) for more information on the Domoticz plugins.*

## How it works

Plugin provides: Status, Control, Fan Level, Battery, Care status devices

**Status**: show current status in readable layout of switch. Status updates by polls 
(interval) and when you click Control device (for instant status change).

**Control**: for sending commands.

**Fan Level**: for adjusting suction power. (MiHome app related: Quiet=38, Balanced=60, Turbo=77, Max=90)

**Battery**: since ```0.0.4``` as new device

**Care**: since ```0.1.0``` new 5 devices (care status + reset tool)

Since ```0.1.0``` plugin uses wrapper-server for python-miio lib. It helps to use this plugin in Domoticz without blocking mode.

## Installation

Before installation plugin check the `python3` and `python3-dev` is installed for Domoticz plugin system:

```sudo apt-get install python3 python3-dev```

Also do note that the setuptools version is too old for installing some requirements, so before trying to install this package you should update the setuptools with:

```sudo pip3 install -U setuptools```.

Also need to install virtualenv:
```sudo pip3 install -U virtualenv```.

Please make sure you have libffi and openssl headers installed, you can do this on Debian-based systems (like Rasperry Pi) with 
```sudo apt-get install libffi-dev libssl-dev```.

Then go to plugins folder and clone plugin then activate virtualenv:
```
cd domoticz/plugins
git clone https://github.com/mrin/domoticz-mirobot-plugin.git xiaomi-mirobot

```

Now create virtualenv and install required libs:
```
cd xiaomi-mirobot
virtualenv -p python3 .env

pip3 install -r pip_req.txt 
# or pip3 install gevent msgpack-python python-miio==0.3.1

```

Restart the Domoticz service
```
sudo service domoticz.sh restart
```

Now go to **Setup** -> **Hardware** in your Domoticz interface and add type with name **Xiaomi Mi Robot Vacuum**.

| Field | Information|
| ----- | ---------- |
| Data Timeout | Keep Disabled |
| IP address | Enter the IP address of your Vacuum (see the MiHome app or router dhcp, should be static) |
| Token |  This token is only attainable before the device has been connected over the app to your local wifi (or alternatively, if you have paired your rooted mobile device with the vacuum, or if you share access to Vacuum via MiHome to rooted device) |
| MIIOServer host:port | Local server will be started with plugin on 127.0.0.1:22222 |
| Update interval | In seconds, this determines with which interval the plugin polls the status of Vacuum. Suggested is no lower then 5 sec due timeout in python-mirobo lib, but you can try any.  |
| Fan Level Type | ```Standard``` - standard set of buttons (values supported by MiHome); ```Slider``` - allow to set custom values, up to 100 (in standard Max=90) (values not supported by MiHome) |
| Python Path | Path to Python 3, default is python3 |
| Debug | When set to true the plugin shows additional information in the Domoticz log |

After clicking on the Add button the new devices are available in **Setup** -> **Devices**.

If you want to change ```Fan Level Type``` just disable hardware, update type and enable again. Old device can be deleted manually in Devices menu.

## How to update plugin

```
cd domoticz/plugins/xiaomi-mirobot
git pull
```

Restart the Domoticz service
```
sudo service domoticz.sh restart
```

## Screenshots

![status_unit](https://user-images.githubusercontent.com/93999/29568433-0da95692-8759-11e7-8706-344c02536d6a.png)
![control_unit](https://user-images.githubusercontent.com/93999/29568435-13645e10-8759-11e7-92d8-5fe130912c78.png)

![fan_level](https://user-images.githubusercontent.com/93999/29668575-6906ea22-88e9-11e7-8508-8f0ff48e2f78.png)
![fan_level2](https://user-images.githubusercontent.com/93999/29713051-86cd023c-89a5-11e7-83cc-5953b8cbbfa5.png)

![care1](https://user-images.githubusercontent.com/93999/32418537-08d3c918-c27d-11e7-89e9-10daf79bcdb4.png)
![care2](https://user-images.githubusercontent.com/93999/32418538-08ef7e10-c27d-11e7-9ff8-8dfff1c20377.png)

![bat](https://user-images.githubusercontent.com/93999/29769383-c8202814-8bf2-11e7-86b2-3629bfc63dc0.png)


### How to obtain device Token

Check the [instruction](https://github.com/rytilahti/python-miio#finding-the-token)
