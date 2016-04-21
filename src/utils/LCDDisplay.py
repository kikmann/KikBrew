'''
Created on Nov 7, 2013

@author: Kikmann, Christian Hellmann
BSD License

Module to use a 4x24 Display
'''
#!/usr/bin/python
import time
import RPi.GPIO as GPIO


# Zuordnung der GPIO Pins (ggf. anpassen)
DISPLAY_RS = 7
DISPLAY_E  = 8
DISPLAY_DATA4 = 25 
DISPLAY_DATA5 = 24
DISPLAY_DATA6 = 23
DISPLAY_DATA7 = 18

DISPLAY_WIDTH = 20      # Zeichen je Zeile
DISPLAY_LINE_1 = 0x80   # Adresse der ersten Display Zeile
DISPLAY_LINE_2 = 0xA8   # Adresse der zweiten Display Zeile
DISPLAY_LINE_3 = 0x94
DISPLAY_LINE_4 = 0xD4
DISPLAY_CHR = True
DISPLAY_CMD = False
E_PULSE = 0.00005
E_DELAY = 0.00005


class LCDDisplay(object):
    '''
    classdocs
    '''


    def __init__(self):
        '''
        Constructor
        '''
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(DISPLAY_E, GPIO.OUT)
        GPIO.setup(DISPLAY_RS, GPIO.OUT)
        GPIO.setup(DISPLAY_DATA4, GPIO.OUT)
        GPIO.setup(DISPLAY_DATA5, GPIO.OUT)
        GPIO.setup(DISPLAY_DATA6, GPIO.OUT)
        GPIO.setup(DISPLAY_DATA7, GPIO.OUT)

    def __del__(self):
        GPIO.cleanup()
            
    def display_init(self):
        self.lcd_byte(0x33,DISPLAY_CMD)
        self.lcd_byte(0x32,DISPLAY_CMD)
        self.lcd_byte(0x28,DISPLAY_CMD)
        self.lcd_byte(0x0C,DISPLAY_CMD)  
        self.lcd_byte(0x06,DISPLAY_CMD)
        self.lcd_byte(0x01,DISPLAY_CMD)  
    
    def write( self, line, message ):
        if line == 1 :
            self.lcd_byte(DISPLAY_LINE_1, DISPLAY_CMD)
        elif line == 2:
            self.lcd_byte(DISPLAY_LINE_2, DISPLAY_CMD)
        elif line == 3:
            self.lcd_byte(DISPLAY_LINE_3, DISPLAY_CMD)
        else:
            self.lcd_byte(DISPLAY_LINE_4, DISPLAY_CMD)
        self.lcd_write(message)

    def lcd_write(self, message):
        message = message.ljust(DISPLAY_WIDTH," ")  
        for i in range(DISPLAY_WIDTH):
            self.lcd_byte(ord(message[i]),DISPLAY_CHR)
    
    def lcd_byte(self, bits, mode):
        GPIO.output(DISPLAY_RS, mode)
        GPIO.output(DISPLAY_DATA4, False)
        GPIO.output(DISPLAY_DATA5, False)
        GPIO.output(DISPLAY_DATA6, False)
        GPIO.output(DISPLAY_DATA7, False)
        if bits&0x10==0x10:
            GPIO.output(DISPLAY_DATA4, True)
        if bits&0x20==0x20:
            GPIO.output(DISPLAY_DATA5, True)
        if bits&0x40==0x40:
            GPIO.output(DISPLAY_DATA6, True)
        if bits&0x80==0x80:
            GPIO.output(DISPLAY_DATA7, True)
        time.sleep(E_DELAY)    
        GPIO.output(DISPLAY_E, True)  
        time.sleep(E_PULSE)
        GPIO.output(DISPLAY_E, False)  
        time.sleep(E_DELAY)      
        GPIO.output(DISPLAY_DATA4, False)
        GPIO.output(DISPLAY_DATA5, False)
        GPIO.output(DISPLAY_DATA6, False)
        GPIO.output(DISPLAY_DATA7, False)
        if bits&0x01==0x01:
            GPIO.output(DISPLAY_DATA4, True)
        if bits&0x02==0x02:
            GPIO.output(DISPLAY_DATA5, True)
        if bits&0x04==0x04:
            GPIO.output(DISPLAY_DATA6, True)
        if bits&0x08==0x08:
            GPIO.output(DISPLAY_DATA7, True)
        time.sleep(E_DELAY)    
        GPIO.output(DISPLAY_E, True)  
        time.sleep(E_PULSE)
        GPIO.output(DISPLAY_E, False)  
        time.sleep(E_DELAY)   
        
