# Xiaomi Mi Robot Vacuum - Domoticz Python plugin

*This plugin uses the [Python-mirobo](https://github.com/rytilahti/python-mirobo) library.*

*See this [link](https://www.domoticz.com/wiki/Using_Python_plugins) for more information on the Domoticz plugins.*

## How it works

Plugin provides 2 devices: Status and Control unit.

**Status unit**: combined from mediaplayer type and vacuum icon for show current status in readable layout of switch. Status updates by polls 
(interval) and when you click Control unit (for instant status change)

**Control unit**: for sending commands.

Plugin calls **python-mirobo** (in subprocess) via own wrapper behind for converting results from lib to JSON and then update status of device.
Domoticz has some limitation in python plugin system, so this lib doesn't work well directly in plugin (plugin halted after first heartbeat).

## Installation

Go to plugins folder and clone plugin:
```
cd domoticz/plugins
git clone https://github.com/mrin/domoticz-mirobot-plugin.git xiaomi-mirobot
```

Please make sure you have libffi and openssl headers installed, you can do this on Debian-based systems (like Rasperry Pi) with ```apt-get install libffi-dev libssl-dev```.
It's required for python-mirobo lib.

Then go to plugin folder and install [python-mirobo](https://github.com/rytilahti/python-mirobo) locally (due issues with python paths) with all dependencies:
```
cd xiaomi-mirobot
pip3 install python-mirobo zeroconf -t .vendors
```

For update python-mirobo use ```pip3 install python-mirobo -t .vendors --upgrade```

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
| Python Path | Path to Python 3, default is python3 |
| Debug | When set to true the plugin shows additional information in the Domoticz log |

After clicking on the Add button the two new devices are available in **Setup** -> **Devices**.

## Screenshots

![status_unit](https://user-images.githubusercontent.com/93999/29568433-0da95692-8759-11e7-8706-344c02536d6a.png)
![control_unit](https://user-images.githubusercontent.com/93999/29568435-13645e10-8759-11e7-92d8-5fe130912c78.png)

### Token on rooted android device

Need file miio2.db. 
```
/data/data/com.xiaomi.smarthome/databases/miio2.db 
```
Open file with any SQLite db editor/manager. Table "devicerecord" with column "token".


