# Xiaomi Mi Robot Vacuum - Domoticz Python plugin

*This plugin uses the [Python-mirobo](https://github.com/rytilahti/python-mirobo) library.*

*See this [link](https://www.domoticz.com/wiki/Using_Python_plugins) for more information on the Domoticz plugins.*

## How it works

Plugin provides: Status, Control, Fan Level and Battery devices.

**Status**: show current status in readable layout of switch. Status updates by polls 
(interval) and when you click Control device (for instant status change).

**Control**: for sending commands.

**Fan Level**: for adjusting suction power. (MiHome app related: Quiet=38, Balanced=60, Turbo=77, Max=90)

**Battery**: since ```0.0.4``` as new device

Plugin calls **python-mirobo** (in subprocess) via own wrapper behind for converting results from lib to JSON and then update status of device.
Domoticz has some limitation in python plugin system, so this lib doesn't work well directly in plugin (plugin halted after first heartbeat).

## Installation

Go to plugins folder and clone plugin:
```
cd domoticz/plugins
git clone https://github.com/mrin/domoticz-mirobot-plugin.git xiaomi-mirobot
```

Please make sure you have libffi and openssl headers installed, you can do this on Debian-based systems (like Rasperry Pi) with ```apt-get install libffi-dev libssl-dev```.

Also do note that the setuptools version is too old for installing some requirements, so before trying to install this package you should update the setuptools with ```pip3 install -U setuptools```.

Then go to plugin folder and install [python-mirobo](https://github.com/rytilahti/python-mirobo) locally (due issues with python paths) with all dependencies:
```
cd xiaomi-mirobot
pip3 install python-mirobo -t .vendors
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

For update python-mirobo use ```pip3 install python-mirobo -t .vendors --upgrade```

Restart the Domoticz service
```
sudo service domoticz.sh restart
```

## Screenshots

![status_unit](https://user-images.githubusercontent.com/93999/29568433-0da95692-8759-11e7-8706-344c02536d6a.png)
![control_unit](https://user-images.githubusercontent.com/93999/29568435-13645e10-8759-11e7-92d8-5fe130912c78.png)

![fan_level](https://user-images.githubusercontent.com/93999/29668575-6906ea22-88e9-11e7-8508-8f0ff48e2f78.png)
![fan_level2](https://user-images.githubusercontent.com/93999/29713051-86cd023c-89a5-11e7-83cc-5953b8cbbfa5.png)

![bat](https://user-images.githubusercontent.com/93999/29769383-c8202814-8bf2-11e7-86b2-3629bfc63dc0.png)

### How to obtain device Token

*Important* For Mi Robot with firmware 3.3.9_003077 or higher use these methods to obtain the device token: https://github.com/jghaanstra/com.xiaomi-miio/blob/master/docs/obtain_token_mirobot_new.md

**Android rooted device** 

*(Also you can share Vacuum via MiHome to the other rooted device)*

Need database file miio2.db which located here: 
```
/data/data/com.xiaomi.smarthome/databases/miio2.db 
```
Open file with any SQLite db editor/manager. Table "devicerecord" with column "token".

**Reset robot**

Install lib and check it
```
pip3 install python-mirobo
mirobo discover
```
You should see something like this:
```
mirobo.vacuum:  IP 192.168.1.12: Xiaomi Mi Robot Vacuum - token: b'ffffffffffffffffffffffffffffffff'
```

Reset the robot, then connect to the network its announcing (SSID "rockrobo-XXXX"). 
Then run ```mirobo discover``` and you should receive token.
