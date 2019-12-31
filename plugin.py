#       
#       Xiaomi Mi Robot Vacuum Plugin
#       Author: mrin, 2017
#       
"""
<plugin key="xiaomi-mi-robot-vacuum" name="Xiaomi Mi Robot Vacuum" author="mrin" version="0.1.3" wikilink="https://github.com/mrin/domoticz-mirobot-plugin" externallink="">
    <params>
        <param field="Mode6" label="MIIOServer host:port" width="200px" required="true" default="127.0.0.1:22222"/>
        <param field="Mode2" label="Update interval (sec)" width="30px" required="true" default="15"/>
        <param field="Mode5" label="Fan Level Type" width="200px">
            <options>
                <option label="Standard (Quiet, Balanced, Turbo, Max)" value="selector" default="true"/>
                <option label="Slider" value="dimmer"/>
            </options>
        </param>
        <param field="Mode4" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" default="true"/>
                <option label="False" value="Normal"/>
            </options>
        </param>
    </params>
</plugin>
"""


import os
import sys

module_paths = [x[0] for x in os.walk( os.path.join(os.path.dirname(__file__), '.', '.env/lib/') ) if x[0].endswith('site-packages') ]
for mp in module_paths:
    sys.path.append(mp)

import Domoticz
import msgpack


class BasePlugin:
    controlOptions = {
        "LevelActions": "||||||",
        "LevelNames": "Off|Clean|Home|Spot|Pause|Stop|Find",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    fanOptions = {
        "LevelActions": "||||",
        "LevelNames": "Off|Quiet|Balanced|Turbo|Max",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }
    careOptions = {
        "LevelActions": "||||",
        "LevelNames": "Off|Main Brush|Side Brush|Filter|Sensor",
        "LevelOffHidden": "true",
        "SelectorStyle": "0"
    }

    customSensorOptions = {"Custom": "1;%"}

    iconName = 'xiaomi-mi-robot-vacuum-icon'

    statusUnit = 1
    controlUnit = 2
    fanDimmerUnit = 3
    fanSelectorUnit = 4
    batteryUnit = 5
    cMainBrushUnit = 6
    cSideBrushUnit = 7
    cSensorsUnit = 8
    cFilterUnit = 9
    cResetControlUnit = 10

    # statuses by protocol
    # https://github.com/marcelrv/XiaomiRobotVacuumProtocol/blob/master/StatusMessage.md
    states = {
        0: 'Unknown 0',
        1: 'Initiating',
        2: 'Sleeping',
        3: 'Waiting',
        4: 'Unknown 4',
        5: 'Cleaning',
        6: 'Back to home',
        7: 'Manual mode',
        8: 'Charging',
        9: 'Charging Error',
        10: 'Paused',
        11: 'Spot cleaning',
        12: 'In Error',
        13: 'Shutting down',
        14: 'Updating',
        15: 'Docking',
        17: 'Zone cleaning',
        100: 'Full'
    }


    def __init__(self):
        self.heartBeatCnt = 0
        self.subHost = None
        self.subPort = None
        self.tcpConn = None
        self.unpacker = msgpack.Unpacker(encoding='utf-8')

    def onStart(self):
        if Parameters['Mode4'] == 'Debug':
            Domoticz.Debugging(1)
            DumpConfigToLog()

        self.heartBeatCnt = 0
        self.subHost, self.subPort = Parameters['Mode6'].split(':')

        self.tcpConn = Domoticz.Connection(Name='MIIOServer', Transport='TCP/IP', Protocol='None',
                                           Address=self.subHost, Port=self.subPort)

        if self.iconName not in Images: Domoticz.Image('icons.zip').Create()
        iconID = Images[self.iconName].ID

        if self.statusUnit not in Devices:
            Domoticz.Device(Name='Status', Unit=self.statusUnit, Type=17,  Switchtype=17, Image=iconID).Create()

        if self.controlUnit not in Devices:
            Domoticz.Device(Name='Control', Unit=self.controlUnit, TypeName='Selector Switch',
                            Image=iconID, Options=self.controlOptions).Create()

        if self.fanDimmerUnit not in Devices and Parameters['Mode5'] == 'dimmer':
            Domoticz.Device(Name='Fan Level', Unit=self.fanDimmerUnit, Type=244, Subtype=73, Switchtype=7,
                            Image=iconID).Create()
        elif self.fanSelectorUnit not in Devices and Parameters['Mode5'] == 'selector':
            Domoticz.Device(Name='Fan Level', Unit=self.fanSelectorUnit, TypeName='Selector Switch',
                                Image=iconID, Options=self.fanOptions).Create()

        if self.batteryUnit not in Devices:
            Domoticz.Device(Name='Battery', Unit=self.batteryUnit, TypeName='Custom', Image=iconID,
                            Options=self.customSensorOptions).Create()

        if self.cMainBrushUnit not in Devices:
            Domoticz.Device(Name='Care Main Brush', Unit=self.cMainBrushUnit, TypeName='Custom', Image=iconID,
                            Options=self.customSensorOptions).Create()

        if self.cSideBrushUnit not in Devices:
            Domoticz.Device(Name='Care Side Brush', Unit=self.cSideBrushUnit, TypeName='Custom', Image=iconID,
                            Options=self.customSensorOptions).Create()

        if self.cSensorsUnit not in Devices:
            Domoticz.Device(Name='Care Sensors ', Unit=self.cSensorsUnit, TypeName='Custom', Image=iconID,
                            Options=self.customSensorOptions).Create()

        if self.cFilterUnit not in Devices:
            Domoticz.Device(Name='Care Filter', Unit=self.cFilterUnit, TypeName='Custom', Image=iconID,
                            Options=self.customSensorOptions).Create()

        if self.cResetControlUnit not in Devices:
            Domoticz.Device(Name='Care Reset Control', Unit=self.cResetControlUnit, TypeName='Selector Switch', Image=iconID,
                            Options=self.careOptions).Create()

        Domoticz.Heartbeat(int(Parameters['Mode2']))


    def onStop(self):
        pass

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("MIIOServer connection status is [%s] [%s]" % (Status, Description))

    def onMessage(self, Connection, Data):
        try:
            self.unpacker.feed(Data)
            for result in self.unpacker:

                Domoticz.Debug("Got: %s" % result)

                if 'exception' in result: return

                if result['cmd'] == 'status':

                    UpdateDevice(self.statusUnit,
                                 (1 if result['state_code'] in [5, 6, 11, 17] else 0), # ON is Cleaning, Back to home, Spot cleaning
                                 self.states.get(result['state_code'], 'Undefined')
                                 )

                    UpdateDevice(self.batteryUnit, result['battery'], str(result['battery']), result['battery'],
                                 AlwaysUpdate=(self.heartBeatCnt % 100 == 0))

                    if Parameters['Mode5'] == 'dimmer':
                        UpdateDevice(self.fanDimmerUnit, 2, str(result['fan_level'])) # nValue=2 for show percentage, instead ON/OFF state
                    else:
                        level = {38: 10, 60: 20, 77: 30, 90: 40}.get(result['fan_level'], None)
                        if level: UpdateDevice(self.fanSelectorUnit, 1, str(level))

                elif result['cmd'] == 'consumable_status':

                    mainBrush = cPercent(result['main_brush'], 300)
                    sideBrush = cPercent(result['side_brush'], 200)
                    filter = cPercent(result['filter'], 150)
                    sensors = cPercent(result['sensor'], 30)

                    UpdateDevice(self.cMainBrushUnit, mainBrush, str(mainBrush), AlwaysUpdate=True)
                    UpdateDevice(self.cSideBrushUnit, sideBrush, str(sideBrush), AlwaysUpdate=True)
                    UpdateDevice(self.cFilterUnit, filter, str(filter), AlwaysUpdate=True)
                    UpdateDevice(self.cSensorsUnit, sensors, str(sensors), AlwaysUpdate=True)

        except msgpack.UnpackException as e:
            Domoticz.Error('Unpacker exception [%s]' % str(e))

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Command '" + str(Command) + "', Level: " + str(Level))

        if self.statusUnit not in Devices:
            Domoticz.Error('Status device is required')
            return

        sDevice = Devices[self.statusUnit]

        if self.statusUnit == Unit:
            if 'On' == Command and self.isOFF:
                if self.apiRequest('start'): UpdateDevice(Unit, 1, self.states[5]) # Cleaning

            elif 'Off' == Command and self.isON:
                if sDevice.sValue == self.states[11] and self.apiRequest('pause'): # Stop if Spot cleaning
                    UpdateDevice(Unit, 0, self.states[3]) # Waiting
                elif self.apiRequest('home'):
                    UpdateDevice(Unit, 1, self.states[6]) # Back to home

        elif self.controlUnit == Unit:

            if Level == 10: # Clean
                if self.apiRequest('start') and self.isOFF:
                    UpdateDevice(self.statusUnit, 1, self.states[5])  # Cleaning

            elif Level == 20: # Home
                if self.apiRequest('home') and sDevice.sValue in [
                    self.states[5], self.states[3], self.states[10]]: # Cleaning, Waiting, Paused
                    UpdateDevice(self.statusUnit, 1, self.states[6])  # Back to home

            elif Level == 30: # Spot
                if self.apiRequest('spot') and self.isOFF and sDevice.sValue != self.states[8]: # Spot cleaning will not start if Charging
                    UpdateDevice(self.statusUnit, 1, self.states[11])  # Spot cleaning

            elif Level == 40: # Pause
                if self.apiRequest('pause') and self.isON:
                    if sDevice.sValue == self.states[11]: # For Spot cleaning - Pause treats as Stop
                        UpdateDevice(self.statusUnit, 0, self.states[3])  # Waiting
                    else:
                        UpdateDevice(self.statusUnit, 0, self.states[10])  # Paused

            elif Level == 50: # Stop
                if self.apiRequest('stop') and self.isON and sDevice.sValue not in [self.states[11], self.states[6]]: # Stop doesn't work for Spot cleaning, Back to home
                    UpdateDevice(self.statusUnit, 0, self.states[3]) # Waiting

            elif Level == 60: # Find
                self.apiRequest('find')

        elif self.fanDimmerUnit == Unit and Parameters['Mode5'] == 'dimmer':
            Level = 1 if Level == 0 else 100 if Level > 100 else Level
            if self.apiRequest('set_fan_level', Level): UpdateDevice(self.fanDimmerUnit, 2, str(Level))

        elif self.fanSelectorUnit == Unit and Parameters['Mode5'] == 'selector':
            num_level = {10: 38, 20: 60, 30: 77, 40: 90}.get(Level, None)
            if num_level and self.apiRequest('set_fan_level', num_level): UpdateDevice(self.fanSelectorUnit, 1, str(Level))

        elif self.cResetControlUnit == Unit:

            if Level == 10: # Reset Main Brush
                if self.apiRequest('care_reset_main_brush'):
                    UpdateDevice(self.cMainBrushUnit, 100, '100')

            elif Level == 20: # Reset Side Brush
                if self.apiRequest('care_reset_side_brush'):
                    UpdateDevice(self.cSideBrushUnit, 100, '100')

            elif Level == 30: # Reset Filter
                if self.apiRequest('care_reset_filter'):
                    UpdateDevice(self.cFilterUnit, 100, '100')

            elif Level == 40: # Reset Sensors
                if self.apiRequest('care_reset_sensor'):
                    UpdateDevice(self.cSensorsUnit, 100, '100')

            self.apiRequest('consumable_status')


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("MIIOServer disconnected")

    def onHeartbeat(self):
        if not self.tcpConn.Connecting() and not self.tcpConn.Connected():
            self.tcpConn.Connect()
            Domoticz.Debug("Trying connect to MIIOServer %s:%s" % (self.subHost, self.subPort))

        elif self.tcpConn.Connecting():
            Domoticz.Debug("Still connecting to MIIOServer %s:%s" % (self.subHost, self.subPort))

        elif self.tcpConn.Connected():
            if self.heartBeatCnt % 30 == 0 or self.heartBeatCnt == 0:
                self.apiRequest('consumable_status')
            self.apiRequest('status')
            self.heartBeatCnt += 1


    @property
    def isON(self):
        return Devices[self.statusUnit].nValue == 1

    @property
    def isOFF(self):
        return Devices[self.statusUnit].nValue == 0

    def apiRequest(self, cmd_name, cmd_value=None):
        if not self.tcpConn.Connected(): return False
        cmd = [cmd_name]
        if cmd_value: cmd.append(cmd_value)
        try:
            self.tcpConn.Send(msgpack.packb(cmd, use_bin_type=True))
            return True
        except msgpack.PackException as e:
            Domoticz.Error('Pack exception [%s]' % str(e))
            return False



def UpdateDevice(Unit, nValue, sValue, BatteryLevel=255, AlwaysUpdate=False):
    if Unit not in Devices: return
    if Devices[Unit].nValue != nValue\
        or Devices[Unit].sValue != sValue\
        or Devices[Unit].BatteryLevel != BatteryLevel\
        or AlwaysUpdate == True:

        Devices[Unit].Update(nValue, str(sValue), BatteryLevel=BatteryLevel)

        Domoticz.Debug("Update %s: nValue %s - sValue %s - BatteryLevel %s" % (
            Devices[Unit].Name,
            nValue,
            sValue,
            BatteryLevel
        ))


def UpdateIcon(Unit, iconID):
    if Unit not in Devices: return
    d = Devices[Unit]
    if d.Image != iconID: d.Update(d.nValue, d.sValue, Image=iconID)

def cPercent(used, max):
    return 100 - round(used / 3600 * 100 / max)


global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data, Status=None, Extra=None):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
