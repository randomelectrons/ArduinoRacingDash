#######################################################
#
#    AC SLI - USB Interface for use with arduino    
#
#    Author: Turnermator13
#
#    Please find this on github at:
#    -https://github.com/Turnermator13/ArduinoRacingDash
#
#    Thanks to @Rombik for "SimInfo"
#
#    Uses pySerial 2.7 library
#    -http://pyserial.sourceforge.net/
#
#######################################################

import sys
sys.path.insert(0, 'apps/python/acSLI/dll')

import ac
import acsys
import math
import serial
import serial.tools.list_ports
from libs.sim_info import SimInfo
from libs.utils import Config

#################
Version = "1.6"
#################

sim_info = SimInfo()
appPath = "apps/python/acSLI/"
appWindow = 0
ser = 0
ticker = 0
port = 0
updateCom = 0

cfg = 0
cfg_Path = "config.ini"
cfg_Port = "AUTO"
cfg_SpeedUnit = "MPH"

max_rpm = 0
max_fuel = 0

lbConnectedPort = 0
lbComPortSetting = 0
btnSpeedUnits = 0
btnReconnect = 0
txtComPort = 0

def acMain(ac_version):
    global appWindow, ticker, cfg_SpeedUnit, cfg_Port, updateCom, btnSpeedUnits, btnReconnect, lbConnectedPort, lbComPortSetting, txtComPort
    appWindow=ac.newApp("AC SLI")
    ac.setSize(appWindow,250,200)
    ac.drawBorder(appWindow,0)
    ac.setBackgroundOpacity(appWindow,0) 
    
    loadConfig()  
    updateCom = 1
  
        
    lbConnectedPort = ac.addLabel(appWindow, "Connected COM Port: {}".format(cfg_Port))
    ac.setPosition(lbConnectedPort,30,40)
    ac.setSize(lbConnectedPort,220,20)
    
    btnReconnect = ac.addButton(appWindow, "Reconnect COM Port")
    ac.addOnClickedListener(btnReconnect, bFunc_ReconnectCOM)
    ac.setPosition(btnReconnect,15,70)
    ac.setSize(btnReconnect,220,20)
       
       
    lbComPortSetting = ac.addLabel(appWindow, "COM Port Setting: ")
    ac.setPosition(lbComPortSetting,30,130)
    ac.setSize(lbComPortSetting,220,20)
    
    txtComPort = ac.addTextInput(appWindow,"COMx")
    ac.setPosition(txtComPort,157,131)
    ac.setSize(txtComPort,50,20)
    ac.addOnValidateListener(txtComPort,txtFunc_ComSetting)
    ac.setText(txtComPort, cfg_Port)
    
    btnSpeedUnits = ac.addButton(appWindow, "Speed Units: {}".format(cfg_SpeedUnit))
    ac.addOnClickedListener(btnSpeedUnits, bFunc_SpeedUnits)
    ac.setPosition(btnSpeedUnits,15,160)
    ac.setSize(btnSpeedUnits,220,20)
    
    
    connectCOM()
    
    ac.console("AC SLI v" + Version + " loaded")
    return "AC SLI"

    
def acUpdate(deltaT):   
    global ticker, ser, max_rpm, max_fuel, sim_info, cfg_SpeedUnit, cfg_Port, updateCom
    
    if ticker == 2:
        ac_gear = ac.getCarState(0, acsys.CS.Gear)
        ac_speed = round(ac.getCarState(0, acsys.CS.SpeedMPH)) if cfg_SpeedUnit == "MPH" else round(ac.getCarState(0, acsys.CS.SpeedKMH))
        rpms = ac.getCarState(0, acsys.CS.RPM)
        max_rpm = sim_info.static.maxRpm if max_rpm == 0 else max_rpm
        
        
        shift = 0
        if max_rpm > 0:
            thresh = max_rpm*0.65
            if rpms >= thresh:
                shift = round(((rpms-thresh)/(max_rpm-thresh))*16)
        
        current_fuel = sim_info.physics.fuel
        max_fuel = sim_info.static.maxFuel if max_fuel == 0 else max_fuel
        fuel = int((current_fuel/max_fuel)*100)
        
        lapCount = sim_info.graphics.completedLaps
        if lapCount > 255:
            lapCount = 255
        
        engine = 0x00
        if sim_info.physics.pitLimiterOn and not sim_info.graphics.isInPit:
            engine = 0x10 

        boost = round(ac.getCarState(0, acsys.CS.TurboBoost), 1)
        b1 = boost*10
            
        key = bytes([255,ac_gear,((int(ac_speed) >> 8) & 0x00FF),(int(ac_speed) & 0x00FF),((int(rpms) >> 8) & 0x00FF),(int(rpms) & 0x00FF),fuel,shift,engine,lapCount, int(b1)])
        x = ser.write(key)
        
        ticker = 0
                
    else:
        if ticker < 3:
            ticker = ticker + 1

    if updateCom == 2:
        ac.setText(txtComPort, cfg_Port)
        updateCom = 1           
    
    
    
def acShutdown():
    global ser
    ser.close()
    
    
def loadConfig():
    global appPath, cfg, cfg_Path, cfg_Port, cfg_SpeedUnit
    
    try:
        cfg = Config(appPath + cfg_Path)
        cfg_Port = cfg.getOption("SETTINGS", "port").upper()
        cfg_SpeedUnit = cfg.getOption("SETTINGS", "unitSpeed").upper()
    
    except Exception as e:
        ac.console("acSLI: Error in loading Config File: %s" % e)
        ac.log("acSLI: Error in loading Config File: %s" % e)
        

def connectCOM():
    global ser, port, cfg_Port, ticker
    
    portValid = False
    for sPort, desc, hwid in sorted(serial.tools.list_ports.comports()):
        if cfg_Port == "AUTO":
            if "Arduino" in desc:
                ac.console("%s: %s [%s]" % (sPort, desc, hwid))
                port = sPort
                portValid = True
        else:                                                                                                   
            if cfg_Port == sPort:
                ac.console("%s: %s [%s]" % (sPort, desc, hwid))
                port = sPort
                portValid = True
        
        if portValid:
            break
                
    if portValid:
        ticker = 0
        ser = serial.Serial(port, 9600)
        ac.console("acSLI: connected to {}".format(port))
    else:
        ticker = 3
        port = "----"
        if cfg_Port == "AUTO": 
            ac.console("acSLI: No Arduino Detected")
        else:
            ac.console("acSLI: Invalid COM Port")
    
    ac.setText(lbConnectedPort, "Connected COM Port: {}".format(port))
    

def txtFunc_ComSetting(string):
    global txtComPort, cfg_Port, updateCom
    text = ac.getText(txtComPort).upper()
    
    cfg_Port = text
    updateCom = 2
    cfg.updateOption("SETTINGS", "port", cfg_Port)
    ac.console("Update COM Port Setting To: {}".format(cfg_Port))

    
def bFunc_ReconnectCOM(dummy, variables):
    global ser
    if not port == "----":
        ser.close()
    connectCOM()  
            
        
def bFunc_SpeedUnits(dummy, variables):
    global cfg, cfg_SpeedUnit, btnSpeedUnits

    if cfg_SpeedUnit == "MPH":
        cfg_SpeedUnit = "KPH"
    elif cfg_SpeedUnit == "KPH":
        cfg_SpeedUnit = "MPH"

    ac.setText(btnSpeedUnits, "Speed Units: {}".format(cfg_SpeedUnit))
    cfg.updateOption("SETTINGS", "unitSpeed", cfg_SpeedUnit)
    ac.console("acSLI: speed units toggle to {}".format(cfg_SpeedUnit))
