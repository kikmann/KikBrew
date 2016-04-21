'''
Created on Nov 7, 2013

@author: Kikmann, Christian Hellmann
BSD License

For a 1wire temperature sensors
'''

import os
import glob
import time


class TempSensor(object):
    '''
    classdocs
    '''

    def __init__(self):
        '''
        Constructor
        '''
        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')
         
        base_dir = '/sys/bus/w1/devices/'
        self.device_folders = glob.glob(base_dir + '28*')
        
        self.device_files = []
        for elem in self.device_folders:
            self.device_files.append( elem + '/w1_slave' ) 

	''' returns number of sensors found '''
    def Count(self):
        return len(self.device_files)

    ''' reads the raw device files (used internally) '''
    def ReadTempRaw(self, device_file):
        f = open(device_file, 'r')
        lines = f.readlines()
        f.close()
        return lines
 
	''' returns temperatures for all sensors as list '''
    def ReadTemp(self):
        ret = []
        
        for elem in self.device_files:
            
            lines = self.ReadTempRaw( elem )
            
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = self.ReadTempRaw( elem )
                
            equals_pos = lines[1].find('t=')
            
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp_c = float(temp_string) / 10
                #temp_f = temp_c * 9.0 / 5.0 + 32.0        # we dont care about Fahrenheit
                ret.append( temp_c )
            else:
                ret.append( -1 )
        
        return ret

