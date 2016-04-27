'''
Created on Jun 27, 2014
@author: kikmann, Christian Hellmann
BSD Licensed

Maischecontroller for 
- HENDI Induktionsheizplatte 3,5kW
- EDIMax smart plug
- 1wire Temperature Sensor
- 4x24 Display

'''
from optparse import OptionParser
import sys, os, time
import datetime
import random

from utils.TempSensor import TempSensor
from utils.LCDDisplay import LCDDisplay
from utils.smartplug import SmartPlug

# the target
def nice( temp ):
    if temp < 0.01 and temp > 0:
        return 0
    return int(temp*100)/100.0

# some global config params
tolerancetemp = 0.25					# heating stops at targettemp - tolerancetemp
tempdifftolerance = 1.0                 # how much diff is acceptable between two measurements (some measurements are broken, need to identify them)
targetstamp = 0

class targetModeEnum:
    nothing = 0
    heating = 1
    holding = 2

class TRController:
    
    def __init__(self):
        self.targettime = []
        self.targettemp = []
        self.targetidx = 0
        self.plug = None
        self.cc = 0
        pass

    def init(self, verbose ):
        
        print "Mashing Controller"
        print "======================="
        print ""
        print
        
        print "Initializing LCD-Display"
        self.LCDDisplay = LCDDisplay()
        self.LCDDisplay.display_init()
        self.LCDDisplay.write(1, "Initializing...")
        
        while True:
            print
            print "Initializing Temperature Sensors"
            self.TempSensors = TempSensor()
            temps = self.TempSensors.ReadTemp()
            print "found "+str(len(temps))+"Sensors"
            self.LCDDisplay.write(2, "found "+str(len(temps))+" Sensors")
            self.cc = 1
            for sensor in temps:
                print "Sensor "+str(self.cc)+" @ "+str(sensor)+" C"
                self.cc += 1
            if len(temps)>0:
                break
        
        print
        print "Initializing SmartPlug"
        self.LCDDisplay.write(3, "...SmartPlug")
        plug = SmartPlug("edimax.fritz.box", ('admin', '1234'))
        print
        print
        
    def checkInitDisplay(self):
        self.cc += 1
        if self.cc == 60 :
            self.cc = 0
            self.LCDDisplay.display_init()      # ocassionaly reinit the display (#1)
        
    
    def readProfile(self):
        self.targettemp = []
        self.targettime = []

        f = open( '/opt/kikbrew/mashing.profile','r' )
        # mashing profile => read & process
        for line in f:
            elems = line.split(",")
            if len(elems)<2:
                print str(datetime.datetime.now())+": invalid format mashing.profile: "+line
            print elems
            self.targettemp.append( float(elems[0]) )
            self.targettime.append( int(elems[1]) )
        f.close()

        # add a final unreachable stage
        self.targettemp.append( 0 )
        self.targettime.append( 999 )
        self.targetidx = 0

    def initialMode(self):
        while True:
            time.sleep(1)
            try:
                f = open( '/opt/kikbrew/stop.mashing','r' )
                f.close()
                # stop mashing exists => no action
                print str(datetime.datetime.now())+": stop mashing exists..."
                temps = self.TempSensors.ReadTemp()
                tmp = temps[0]/100.0
                self.LCDDisplay.write(4, "stopped -- "+str(nice(tmp))+"C  ")
                continue
            except IOError as e:
                pass    # assume not found

            try:
                self.readProfile()
                break
            except IOError as e:
                print str(datetime.datetime.now())+": mashing.profile does not exist !"
                continue # assume not found


            
    def run(self):
        p.state = "ON"

        self.targetidx  = 0
        targetmode = targetModeEnum.heating
        targetstamp = datetime.datetime.now()
        passedtime  = 0
        self.cc = 0
        oldtemp = -1

        print self.targettemp
        print self.targettime
        print self.targetidx
        
        while True:
            timestamp = datetime.datetime.now()

            # test for pauzing
            activated = False
            try:
                while True:     # pause as long as the file exists
                    f = open( '/opt/kikbrew/pause.mashing','r' )
                    f.close()
                    activated = True
                    # pause mashing exists => pauze!
                    print str(timestamp)+": pause mashing exists..."
                    temps = self.TempSensors.ReadTemp()
                    tmp = temps[0]/100.0
                    self.checkInitDisplay()
                    self.LCDDisplay.write(4, "pauzed - "+str(nice(tmp))+"C  ")
                    time.sleep( 1 )
                    p.state = "OFF"
                    oldtemp = -1       # accept any new temp
                    continue
            
            except IOError as e:
                if activated and targetmode == targetModeEnum.heating :    # switch it on again
					p.state = "ON"
            
            # test for stopping
            activated = False
            try:
                while True:     # stop if file exists
                    f = open( '/opt/kikbrew/stop.mashing','r' )
                    f.close()
                    activated = True
                    # stop mashing exists => stop it !
                    print str(timestamp)+": stop mashing exists..."
                    temps = self.TempSensors.ReadTemp()
                    tmp = temps[0]/100.0
                    self.checkInitDisplay()
                    self.LCDDisplay.write(4, "mashing stopped - "+str(nice(tmp))+"C  ")
                    time.sleep(1)
                    p.state = "OFF"
                    oldtemp = -1    # accept any new temp
            
            except IOError as e:
                if activated and targetmode == targetModeEnum.heating :    # switch it on again
                    self.readProfile()
                    p.state = "ON"
            
            # try to get a reasonable temp
            tries = 0
            while True:            
                tries += 1
                # get the temperatures
                temps = self.TempSensors.ReadTemp()
                #temps = ( int(random.random()*2500), int(random.random()*2500) )
                # setup has to be that sensor 1 is in the brew
                temp = temps[0]/100.0

                # check wether this temp makes any sense
                if oldtemp == -1 :    # no previous value, therefore accept the value
                    break

                if abs(temp - oldtemp) < tempdifftolerance :  # acceptable difference
                    break

                # too much difference
                if tries == 3 :
                    break   # three outliers are no outliers anymore
                
                # .... and again !

            oldtemp = temp

            # print it to the LCD
            self.LCDDisplay.write( 1, "Mashingcontrol" )
            self.LCDDisplay.write( 2, str(nice(temp))+"C-"+str(self.targettemp[self.targetidx])+"C-"+str(self.targettime[self.targetidx])+"min" )
            self.LCDDisplay.write( 3, "Mode:"+str(targetmode) )
            self.LCDDisplay.write( 4, " " )
            
            # wait until next minute
            time.sleep(0.3)
            
            self.checkInitDisplay()
                            
            # adjust to target temperature

            if targetmode == targetModeEnum.heating and self.targettemp[self.targetidx] - tolerancetemp < temp :
                # reached target temperature
                targetmode = targetModeEnum.holding
                targetstamp = datetime.datetime.now()
                p.state = "OFF"

            if targetmode == targetModeEnum.holding :
                passedtime += 1

                if (datetime.datetime.now()-targetstamp).seconds > self.targettime[self.targetidx]*60 :
                    # held long enough, next rast
                    targetmode = targetModeEnum.heating
                    self.targetidx += 1
                    passedtime = 0
                    p.state = "ON"

            print str(timestamp)+", running, "+str(temp)+","+str(targetmode)+","+str(self.targettemp[self.targetidx])+","+str(self.targettime[self.targetidx])+","+str(passedtime)+"\n"
            # record data
            f = open( "/opt/kikbrew/mashing.log", "a" )
            f.write( str(timestamp)+", running, "+str(temp)+","+str(targetmode)+","+str(self.targettemp[self.targetidx])+","+str(self.targettime[self.targetidx])+","+str(passedtime)+"\n" )
            f.close()
            
        pass

if __name__ == '__main__':
    parser = OptionParser()
    parser.set_usage("usage: %prog [options]")
    parser.add_option( "-v", "--verbose", dest="verbose", action="store_true", default=False, help="verbose output" )
    (options, args) = parser.parse_args()
    
    ctrl = TRController()
        
    ctrl.init( options.verbose )
    
    while True:
        ctrl.initialMode()
        ctrl.run()
    
'''
27-04-16    #1    every 60 seconds init display, even in pause & stop
27-04-16    #5    should run even if smartplug is not present


'''