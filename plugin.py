#       
#       Xiaomi Mi Robot Vacuum Plugin
#       Author: mrin, 2017
#       
"""
<plugin key="xiaomi-mi-robot-vacuum" name="Xiaomi Mi Robot Vacuum" author="mrin" version="0.0.2" wikilink="https://github.com/mrin/domoticz-mirobot-plugin" externallink="">
    <params>
        <param field="Address" label="IP address" width="200px" required="true" default="192.168.1.12"/>
        <param field="Mode1" label="Token" width="200px" required="true" default="476e6b70343055483230644c53707a12"/>
        <param field="Mode2" label="Update interval (sec)" width="30px" required="true" default="15"/>
        <param field="Mode3" label="Fan Level Type" width="200px">
            <options>
                <option label="Standard (Quiet, Balanced, Turbo, Max)" value="selector" default="true"/>
                <option label="Slider" value="dimmer"/>
            </options>
        </param>
        <param field="Mode4" label="Python Path" width="200px" required="true" default="python3"/>
        <param field="Mode5" label="Debug" width="75px">
            <options>
                <option label="True" value="Debug" default="true"/>
                <option label="False" value="Normal"/>
            </options>
        </param>
    </params>
</plugin>
"""

import Domoticz
import subprocess
import os
import json


class BasePlugin:
    enabled = False
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

    iconName = 'XiaomiRobotVacuum'

    statusUnit = 1
    controlUnit = 2
    fanDimmerUnit = 3
    fanSelectorUnit = 4

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
        100: 'Full'
    }

    def onStart(self):
        if Parameters['Mode5'] == 'Debug':
            Domoticz.Debugging(1)
            DumpConfigToLog()

        if self.iconName not in Images: Domoticz.Image('icons.zip').Create()
        iconID = Images[self.iconName].ID

        if self.statusUnit not in Devices:
            Domoticz.Device(Name='Status', Unit=self.statusUnit, Type=17,  Switchtype=17, Image=iconID).Create()

        if self.controlUnit not in Devices:
            Domoticz.Device(Name='Control', Unit=self.controlUnit, TypeName='Selector Switch',
                            Image=iconID, Options=self.controlOptions).Create()

        if self.fanDimmerUnit not in Devices and Parameters['Mode3'] == 'dimmer':
            Domoticz.Device(Name='Fan Level', Unit=self.fanDimmerUnit, Type=244, Subtype=73, Switchtype=7,
                            Image=iconID).Create()

        elif self.fanSelectorUnit not in Devices and Parameters['Mode3'] == 'selector':
            Domoticz.Device(Name='Fan Level', Unit=self.fanSelectorUnit, TypeName='Selector Switch',
                                Image=iconID, Options=self.fanOptions).Create()

        Domoticz.Heartbeat(int(Parameters['Mode2']))


    def onStop(self):
        Domoticz.Debug("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called")

    def onMessage(self, Connection, Data, Status, Extra):
        Domoticz.Debug("onMessage called")

    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Command '" + str(Command) + "', Level: " + str(Level))

        if self.statusUnit not in Devices:
            Domoticz.Error('Status device is required')
            return
            
        sDevice = Devices[self.statusUnit]
        
        if self.statusUnit == Unit:
            if 'On' == Command and self.isOFF:
                if callWrappedCommand('start'): UpdateDevice(Unit, 1, self.states[5]) # Cleaning
            
            elif 'Off' == Command and self.isON:
                if sDevice.sValue == self.states[11] and callWrappedCommand('pause'): # Stop if Spot cleaning
                    UpdateDevice(Unit, 0, self.states[3]) # Waiting
                elif callWrappedCommand('home'):
                    UpdateDevice(Unit, 1, self.states[6]) # Back to home

        elif self.controlUnit == Unit:
            
            if Level == 10: # Clean
                if callWrappedCommand('start') and self.isOFF:
                    UpdateDevice(self.statusUnit, 1, self.states[5])  # Cleaning
                    
            elif Level == 20: # Home
                if callWrappedCommand('home') and sDevice.sValue in [
                    self.states[5], self.states[3], self.states[10]]: # Cleaning, Waiting, Paused
                    UpdateDevice(self.statusUnit, 1, self.states[6])  # Back to home
            
            elif Level == 30: # Spot
                if callWrappedCommand('spot') and self.isOFF and sDevice.sValue != self.states[8]: # Spot cleaning will not start if Charging
                    UpdateDevice(self.statusUnit, 1, self.states[11])  # Spot cleaning
            
            elif Level == 40: # Pause
                if callWrappedCommand('pause') and self.isON:
                    if sDevice.sValue == self.states[11]: # For Spot cleaning - Pause treats as Stop
                        UpdateDevice(self.statusUnit, 0, self.states[3])  # Waiting
                    else:
                        UpdateDevice(self.statusUnit, 0, self.states[10])  # Paused
            
            elif Level == 50: # Stop
                if callWrappedCommand('stop') and self.isON and sDevice.sValue not in [self.states[11], self.states[6]]: # Stop doesn't work for Spot cleaning, Back to home
                    UpdateDevice(self.statusUnit, 0, self.states[3]) # Waiting
                
            elif Level == 60: # Find 
                callWrappedCommand('find')

        elif self.fanDimmerUnit == Unit and Parameters['Mode3'] == 'dimmer':
            Level = 1 if Level == 0 else 100 if Level > 100 else Level
            if callWrappedCommand('fan_level', Level): UpdateDevice(self.fanDimmerUnit, 2, str(Level))

        elif self.fanSelectorUnit == Unit and Parameters['Mode3'] == 'selector':
            num_level = {10: 38, 20: 60, 30: 77, 40: 90}.get(Level, None)
            if num_level and callWrappedCommand('fan_level', num_level): UpdateDevice(self.fanSelectorUnit, 1, str(Level))


    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called")

    def onHeartbeat(self):
        result = callWrappedCommand('status')
        if not result or 'state_code' not in result or 'error_code' in result: return

        UpdateDevice(self.statusUnit,
                     (1 if result['state_code'] in [5, 6, 11] else 0), # ON is Cleaning, Back to home, Spot cleaning
                     self.states.get(result['state_code'], 'Undefined'),
                     result['battery'])

        if Parameters['Mode3'] == 'dimmer':
            UpdateDevice(self.fanDimmerUnit, 2, str(result['fan_level'])) # nValue=2 for show percentage, instead ON/OFF state
        else:
            level = {38: 10, 60: 20, 77: 30, 90: 40}.get(result['fan_level'], None)
            if level: UpdateDevice(self.fanSelectorUnit, 1, str(level))

    @property              
    def isON(self):
        return Devices[self.statusUnit].nValue == 1
    
    @property
    def isOFF(self):
        return Devices[self.statusUnit].nValue == 0


def callWrappedCommand(cmd_name=None, cmd_value=None):
    call_params = [Parameters['Mode4'], os.path.dirname(__file__) + '/mirobo-wrapper.py', Parameters['Address'], Parameters['Mode1']]
    if cmd_name: call_params.append(cmd_name)
    if cmd_value: call_params.append(str(cmd_value))

    try:
        call_resp = subprocess.check_output(call_params, universal_newlines=True)
        Domoticz.Debug(call_resp)
        
        try:
            result = json.loads(call_resp)
            if 'exception' in result:
                Domoticz.Error('Response mirobo-wrapper exception: %s' % result['exception'])
                return None
            return result
            
        except Exception:
            Domoticz.Error('callWrappedCommand() json parse exception')
            return None
            
    except Exception as e:
        Domoticz.Error('Call mirobo-wrapper exception: %s' % str(e))
        return None


def UpdateDevice(Unit, nValue, sValue, BatteryLevel=255, AlwaysUpdate=False):
    if Unit not in Devices: return
    if Devices[Unit].nValue != nValue\
        or Devices[Unit].sValue != sValue\
        or Devices[Unit].BatteryLevel != BatteryLevel\
        or AlwaysUpdate == True:

        if BatteryLevel == 255: BatteryLevel = Devices[Unit].BatteryLevel
        Devices[Unit].Update(nValue, str(sValue), BatteryLevel=BatteryLevel)

        Domoticz.Debug("Update %s: nValue %s - sValue %s - BatteryLevel %s" % (
            Devices[Unit].Name,
            nValue,
            sValue,
            BatteryLevel
        ))


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

def onMessage(Connection, Data, Status, Extra):
    global _plugin
    _plugin.onMessage(Connection, Data, Status, Extra)

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