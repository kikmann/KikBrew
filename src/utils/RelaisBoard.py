'''
Created on Nov 7, 2013

@author: Kikmann, Christian Hellmann
BSD License

Control over four relais (controlling cooking plates)
'''
import RPi.GPIO as GPIO

# which GPIO pins are used for the four relais
RELAIS_ONE = 17
RELAIS_TWO = 27
RELAIS_THREE = 22
RELAIS_FOUR  = 10

class RelaisBoard(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        GPIO.setmode(GPIO.BCM)
        
        GPIO.setup(RELAIS_ONE, GPIO.OUT)
        GPIO.setup(RELAIS_TWO, GPIO.OUT)
	GPIO.setup(RELAIS_THREE, GPIO.OUT)
	GPIO.setup(RELAIS_FOUR, GPIO.OUT)
        
        self.RelaisOneOff()
        self.RelaisTwoOff()
	self.RelaisThreeOff()
	self.RelaisFourOff()

        
    def RelaisOneOn(self):
        GPIO.output(RELAIS_ONE, False)       # means 'off'  

    
    def RelaisOneOff(self):
        GPIO.output(RELAIS_ONE, True)       # means 'off'  

    
    def RelaisTwoOn(self):
        GPIO.output(RELAIS_TWO, False)       # means 'off'  


    def RelaisTwoOff(self):
        GPIO.output(RELAIS_TWO, True)       # means 'off'  

        
    def RelaisThreeOn(self):
	GPIO.output(RELAIS_THREE, False)

    def RelaisThreeOff(self):
	GPIO.output(RELAIS_THREE, True)

    def RelaisFourOn(self):
        GPIO.output(RELAIS_FOUR, False)

    def RelaisFourOff(self):
        GPIO.output(RELAIS_FOUR, True)

        
