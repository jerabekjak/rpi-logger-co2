import drivers
import RPi.GPIO as GPIO
from time import sleep
from datetime import datetime
from sgp30 import SGP30
import time
import sys
import glob
import os
import numpy as np

#disable warnings (optional)
GPIO.setwarnings(False)
#Select GPIO Mode
GPIO.setmode(GPIO.BCM)
#set red,green and blue pins
redPin = 12
greenPin = 19
bluePin = 13
#set pins as outputs
GPIO.setup(redPin,GPIO.OUT)
GPIO.setup(greenPin,GPIO.OUT)
GPIO.setup(bluePin,GPIO.OUT)

def turnoff():
    GPIO.output(redPin,GPIO.HIGH)
    GPIO.output(greenPin,GPIO.HIGH)
    GPIO.output(bluePin,GPIO.HIGH)

def red():
    GPIO.output(redPin,GPIO.LOW)
    GPIO.output(greenPin,GPIO.HIGH)
    GPIO.output(bluePin,GPIO.HIGH)

display = drivers.Lcd()

class SGP30_Raw(SGP30):
    def get_air_quality_raw(self):
        eco2, tvoc = self.command('measure_air_quality')
        reco2, rtvoc = self.command('measure_raw_signals')
        return (eco2, tvoc, reco2, rtvoc)


class Temp(object):

    def __init__(self):

        os.system('modprobe w1-gpio')
        os.system('modprobe w1-therm')

        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')
        self._device_file = [df + '/w1_slave' for df in device_folder] 


    def _read_temp_raw(self,df):
        f = open(df, 'r')
        lines = f.readlines()
        f.close()
        return lines

    def read(self):
        temp_c = []
        for idf in self._device_file :
            lines = self._read_temp_raw(idf)
            while lines[0].strip()[-3:] != 'YES':
                time.sleep(0.2)
                lines = read_temp_raw(idf)
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos+2:]
                temp = float(temp_string) / 1000.0
            temp_c.append(temp)
        return temp_c



sgp30 = SGP30_Raw()
display.lcd_display_string("LOVE YOU", 1)  # Write line of text to first line of display
turnoff()

print("Calculating calibration curve...")

datapath = '{}/{}'.format(os.path.dirname(os.path.realpath(__file__)), 'data.csv')

data = np.loadtxt(datapath, delimiter=';', skiprows=1)
y = data[:,0]
x = data[:,1]


p = np.polyfit(x, y, 1)

m = p[0]
c = p[1]

print('calibration line is {0:4.2f}x + {1:4.2f}'.format(m,c))

temp = Temp()

print("Sensor warming up, please wait...")
def crude_progress_bar():
    sys.stdout.write('.')
    sys.stdout.flush()

sgp30.start_measurement(crude_progress_bar)
sys.stdout.write('\n')
#sgp30.command('init_air_quality')
#print (sgp30.command('measure_test'))

red()

sleep_time = 1.0

try:
    print("Writing to display")
    while True:
        # Write just the time to the display

        result = sgp30.get_air_quality()
        raw = sgp30.get_air_quality_raw()
        # if (raw[0] == 400): print (raw)
        calibvals = m*raw[2]+c - 100

        t1= time.time()
        tt = temp.read()
        t2 = time.time() - t1

        if (tt[0] < 10): 
            turnoff()
            sleep(0.05)
            red()
            sleep(0.05)
            turnoff()
            sleep(0.05)
            red()
            sleep(0.05)
            turnoff()
            sleep(0.05)
            red()
            sleep_time = 1.0 - 4*0.05
        if (tt[0] > 30): 
            turnoff()
            sleep(0.05)
            red()
            sleep(0.05)
            turnoff()
            sleep(0.05)
            red()
            sleep(0.05)
            turnoff()
            sleep(0.05)
            red()
            sleep_time = 1.0 - 4*0.05
        if (calibvals > 900): 
            turnoff()
            sleep(0.05)
            red()
            sleep(0.05)
            turnoff()
            sleep(0.05)
            red()
            sleep(0.05)
            turnoff()
            sleep(0.05)
            red()
            sleep_time = 1.0 - 4*0.05

        # print(t2)
        display.lcd_clear()
        print ('{};{};{};{};{};{};{};{}'.format(datetime.now().date(),datetime.now().time(),raw[0],raw[1],raw[2],raw[3],round(calibvals,0), str(tt[0])))
        display.lcd_display_string('co2e: {} ppm'.format(str(round(calibvals,0))), 1)
        #display.lcd_display_string('co2e: {} ppm'.format(str(raw[0])), 1)
        #display.lcd_display_string('raw sig.: {}'.format(str(raw[2])), 2)
        display.lcd_display_string('temp.: {}'.format(str(tt[0])), 2)
        # Uncomment the following line to loop with 1 sec delay
        #sleep(sleep_time)
        sleep_time = 1.0

except KeyboardInterrupt:
    # If there is a KeyboardInterrupt (when you press ctrl+c), exit the program and cleanup
    print("Cleaning up!")
    display.lcd_clear()
