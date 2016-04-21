'''
Created on Jun 27, 2014
@author: kikmann, Christian Hellmann
BSD Licensed

Maischecontroller for 
- 4 hotplates 1,5kw
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
from utils.RelaisBoard import RelaisBoard

# the target
def nice( temp ):
    if temp < 0.01 and temp > 0:
        return 0
    return int(temp*100)/100.0

# some globals
tolerancetemp = 0.5
targettemp = []
targettime = []
targetidx  = 0
targetstamp = 0

class targetModeEnum:
    nothing = 0
    heating = 1
    holding = 2

# for the temperature state machine
class heatModeEnum:
    nothing = 0
    heating = 1
    cooling = 2


class TRController:
    
    def __init__(self):
        self.heatpct     = 1  # *100
        self.timeslice   = 10   # sec
        self.heatMode    = heatModeEnum.nothing    # 1 = heating, 2=cooling
        self.heatCounter = 0
        self.projectionTime = 6*60  # projection of 10 minutes into the future
        
        self.stirrpct    = 0.
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
            cc = 1
            for sensor in temps:
                print "Sensor "+str(cc)+" @ "+str(sensor)+" C"
                cc += 1
            if len(temps)>0:
                break
        
        print
        print "Initializing RelaisBoard"
        self.LCDDisplay.write(3, "...Releaisboard")
        self.RelaisBoard = RelaisBoard()
        self.RelaisBoard.RelaisOneOff()
        self.RelaisBoard.RelaisTwoOff()
        self.RelaisBoard.RelaisThreeOff()
        self.RelaisBoard.RelaisFourOff()

        print
        print
        
    def initialMode(self):
        while True:
            time.sleep(1)
            try:
                f = open( '/opt/kikbrew/stop.mashing','r' )
                f.close()
                # stop mashing exists => no action
                print str(datetime.datetime.now())+": stop mashing exists..."
                self.LCDDisplay.write(4, "mashing stopped")
                continue
            except IOError as e:
                pass    # assume not found

            try:
                f = open( '/opt/kikbrew/mashing.profile','r' )
                # mashing profile => read & process
                for line in f:
                    elems = line.split(",")
                    if len(elems)<2:
                        print str(datetime.datetime.now())+": invalid format mashing.profile: "+line                        
		    print elems
                    targettemp.append( float(elems[0]) )
                    targettime.append( int(elems[1]) )
                f.close()
                
                # add a final unreachable stage
                targettemp.append( 0 )
                targettime.append( 999 )

                break
                
            except IOError as e:
                print str(datetime.datetime.now())+": mashing.profile does not exist !"
                continue # assume not found
            
            
    def run(self):
        self.heatMode    = heatModeEnum.heating
        self.heatCounter = self.heatpct * self.timeslice
        
        self.RelaisBoard.RelaisOneOn()    # stirrer on
        time.sleep(0.3)
        self.RelaisBoard.RelaisTwoOn()
        time.sleep(0.3)
        self.RelaisBoard.RelaisThreeOn()
        time.sleep(0.3)
        self.RelaisBoard.RelaisFourOn()
        lastTemp = -1
        projtemp = 0
        targetidx  = 0
        targetmode = targetModeEnum.heating
        targetstamp = datetime.datetime.now()
        passedtime  = 0
        
        while True:
            timestamp = datetime.datetime.now()

            # test for pauzing
            try:
                while True:     # pause as long as the file exists
                    f = open( '/opt/kikbrew/pause.mashing','r' )
                    f.close()
                    # pause mashing exists => pauze!
                    print str(timestamp)+": pause mashing exists..."
                    self.LCDDisplay.write(4, "mashing pauzed")
                    time.sleep( 1 )
                    self.RelaisBoard.RelaisOneOff()    # stirrer on
                    self.RelaisBoard.RelaisTwoOff()   # but heating off
                    self.RelaisBoard.RelaisThreeOff()
                    self.RelaisBoard.RelaisFourOff()
                    continue
            
            except IOError as e:
                pass    # assume not found, which is good....
            
            # test for stopping
            try:
                while True:     # stop if file exists
                    f = open( '/opt/kikbrew/stop.mashing','r' )
                    f.close()
                    # stop mashing exists => stop it !
                    print str(timestamp)+": stop mashing exists..."
                    self.LCDDisplay.write(4, "mashing stopped")
                    self.RelaisBoard.RelaisOneOff()    # stirrer off
                    self.RelaisBoard.RelaisTwoOff()   # and heating off
                    self.RelaisBoard.RelaisThreeOff()    
                    self.RelaisBoard.RelaisFourOff()        
                    return
            
            except IOError as e:
                pass    # assume not found, which is good....
            
            
            # get the temperatures
            temps = self.TempSensors.ReadTemp()
            #temps = ( int(random.random()*2500), int(random.random()*2500) )
            # setup has to be that sensor 1 is in the brew
            temp = temps[0]/100.0
            
            if lastTemp == -1: lastTemp = temp
            # print it to the LCD
            self.LCDDisplay.write( 1, "Mashingcontrol" )
            self.LCDDisplay.write( 2, str(nice(temp))+"C-"+str(targettemp[targetidx])+"C-"+str(targettime[targetidx])+"min" )
            self.LCDDisplay.write( 3, str(self.heatCounter)+"s Mode:"+str(self.heatMode) )
            self.LCDDisplay.write( 4, str(nice(100.0*self.heatpct))+"% --> "+str(projtemp)+"C" )
            
            # wait until next minute
            time.sleep(0.3)
            # decrease the heatCounter and process a potential change            
            self.heatCounter -= 1
            
            while self.heatCounter <= 0 :
                # after heating comes the cooling
                if self.heatMode == heatModeEnum.heating :
                    if self.heatpct < 0.99 :
                        self.RelaisBoard.RelaisOneOff()
                        self.RelaisBoard.RelaisTwoOff()
                        self.RelaisBoard.RelaisThreeOff()
                        self.RelaisBoard.RelaisFourOff()
                    self.heatMode = heatModeEnum.cooling
                    self.heatCounter = (1-self.heatpct) * self.timeslice
                    continue
                
                # after cooling comes the recalibration
                if self.heatMode == heatModeEnum.cooling :
                    
                    self.LCDDisplay.display_init()      # ocassionaly reinit the display  
                    # adjust to target temperature
                    # projection <n> min in future with current temperature change
                    projtemp = temp +  (temp - lastTemp) * self.projectionTime / self.timeslice
                    
                    #if targetmode == targetModeEnum.heating and targettemp[targetidx] - tolerancetemp < temp < targettemp[targetidx] + tolerancetemp:
                    if targetmode == targetModeEnum.heating and targettemp[targetidx] - tolerancetemp < temp :    # do not check for correct cooling
                        # reached target temperature
                        targetmode = targetModeEnum.holding
                        targetstamp = datetime.datetime.now()
                        
                    if targetmode == targetModeEnum.holding :
                        passedtime += self.timeslice
                        
                        if (datetime.datetime.now()-targetstamp).seconds > targettime[targetidx]*60 :
                            # held long enough, next rast
                            targetmode = targetModeEnum.heating
                            targetidx += 1
                            passedtime = 0
                    
                    #if temp < targettemp[targetidx] - tolerancetemp and  projtemp > targettemp[targetidx] + tolerancetemp :
		    if projtemp > targettemp[targetidx] + tolerancetemp :
                        # projected temperature too hot => reduce heating
                        if self.heatpct > 0.05 :
                            self.heatpct -= 1
                        
                    if projtemp < targettemp[targetidx] - tolerancetemp :
                        # projected temperature too cold => increase heating
                        if self.heatpct < 0.95 :
                            self.heatpct += 1
                    
                    if self.heatpct > 0.01 :
                        self.RelaisBoard.RelaisOneOn()
                        time.sleep(0.3)
                        self.RelaisBoard.RelaisTwoOn()
                        time.sleep(0.3)
                        self.RelaisBoard.RelaisThreeOn()
                        time.sleep(0.3)
                        self.RelaisBoard.RelaisFourOn()
                        
                    self.heatMode = heatModeEnum.heating
                    self.heatCounter = self.heatpct * self.timeslice
                    lastTemp = temp
                    #time.sleep(0.5)    # give it some time to let init (next line) work
                    #self.LCDDisplay.display_init()
                    continue
                
            # record data
            print str(timestamp)+", "+str(temp)+", "+str(self.heatMode)+", "+str(self.heatCounter)+", "+str(self.heatpct)+", "+str(projtemp)
            f = open( "/opt/kikbrew/mashing.log", "a" )
            f.write( str(timestamp)+", running, "+str(temp)+", "+str(self.heatMode)+", "+str(self.heatCounter)+", "+str(self.heatpct)+", "+str(projtemp)+","+str(targetmode)+","+str(targettemp[targetidx])+","+str(targettime[targetidx])+","+str(passedtime)+"\n" )
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

Webinterface (Mobil):

Status    :    ON/OFF
Updatezeit:    <timestamp> 
Temperatur:    <act>C / <target>C (current)
Haltezeit :    <passed>min / <rasttime>min (if running)

[Historygraph]

Konfiguration:
Rast    Temperatur    Haltezeit
1        ___            ___
2        ___            ___
3        ___            ___
4        ___            ___
5        ___            ___

START / STOP / PAUZE


*****************


START  -> write mashing.profile, remove stop.mashing, remove pauze.mashing
STOP   -> write stop.mashing
PAUZE  -> write pauze.mashing
RESUME -> remove pauze.mashing


+ mashing control starts at boot time
    stdout is redirected to /opt/kikbrew/mashing.stdout
    
+ initial mode, repeated checks:
    + if /opt/kikbrew/stop.mashing exists, nothing is done
    + if /opt/kikbrew/mashing.profile exists, then it is read and processing is started => processing mode
      File contains lines for each Rast:  Rasttemperature, Rasttime

+ processing mode, repeated checks:    
    + if during processing the file /opt/kikbrew/pause.mashing is found, processing is paused until this file
        is removed
    + if during processing the file /opt/kikbrew/stop.mashing is found, processing is stopped => initial mode
    

'''

