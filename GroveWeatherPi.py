import logging
import logging.config
import math
import MySQLdb as mdb
import os
import random 
import re
import RPi.GPIO as GPIO
import smbus
import struct
import subprocess
import sys
import time
import urllib2 

from datetime import datetime
from service import find_syslog, Service

sys.path.append('./SDL_Pi_SSD1306')
sys.path.append('./Adafruit_Python_SSD1306')
sys.path.append('./RTC_SDL_DS3231')
sys.path.append('./Adafruit_Python_BMP')
sys.path.append('./Adafruit_Python_GPIO')
sys.path.append('./SDL_Pi_WeatherRack')
sys.path.append('./max44009')

import SDL_DS3231
import Adafruit_BMP.BMP280 as BMP280
import SDL_Pi_WeatherRack as SDL_Pi_WeatherRack
import Adafruit_SSD1306
import Scroll_SSD1306
import WeatherUnderground
import max44009 as MAX44009
from tentacle_pi.AM2315 import AM2315

logging.config.fileConfig('logging.conf')
logger = logging.getLogger(__name__)

# MySQL configuration
MySQL_Enable = False
MySQL_Url = 'localhost'
MySQL_User = 'root'
MySQL_Password = "password"
MySQL_Database = 'GroveWeatherPi'

# WeatherUnderground Station
WeatherUnderground_Enable = False
WeatherUnderground_StationID = "KWXXXXX"
WeatherUnderground_StationKey = "YYYYYYY"

#WeatherRack Weather Sensors
#GPIO Numbering Mode GPIO.BCM
anemometerPin = 23
rainPin = 24

# constants
SDL_MODE_INTERNAL_AD = 0
SDL_MODE_I2C_ADS1015 = 1

#sample mode means return immediately.  The wind speed is averaged at sampleTime or when you ask, whichever is longer
SDL_MODE_SAMPLE = 0 
SDL_MODE_DELAY = 1 #Delay mode means to wait for sampleTime and the average after that time.

# OLED SSD_1306 Setup
RST = 27

class GroveWeatherPi:
    # Load Devices
	weatherStation = SDL_Pi_WeatherRack.SDL_Pi_WeatherRack(anemometerPin, rainPin, 0,0, SDL_MODE_I2C_ADS1015)
	ds3231 = SDL_DS3231.SDL_DS3231(1, 0x68)
	bmp280 = BMP280.BMP280()
	max44009 = MAX44009.MAX44009(1, 0x4a)
	display = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)
	am2315 = AM2315(0x5c,"/dev/i2c-1")

    # initialize appropriate weather variables
    currentWindDirection = 0
	currentWindDirectionVoltage = 0.0
	rain60Minutes = 0.0
	totalRain = 0
    rainArray = []
	lastRainReading = 0.0

    def __init__(self):
    	self.weatherStation.setWindMode(SDL_MODE_SAMPLE, 5.0)
		self.ds3231.write_now()
		self.ds3231.read_datetime()
		self.max44009.configure(0, 0, 0, 0)
		self.display.begin()
		self.display.clear()
		self.display.display()
		outsideTemperature, outsideHumidity, crc_check = self.am2315.sense() 
        for i in range(20):
    		self.rainArray.append(0)

	def addRainToArray(self, plusRain):
		del self.rainArray[0]
		self.rainArray.append(plusRain)

	def totalRainArray(self):
		total = 0
		for i in range(20):
			total = total+rainArray[i]
		return total

	def sampleAndDisplay(self):
		self.currentWindSpeed = self.weatherStation.current_wind_speed()
		self.currentWindGust = self.weatherStation.get_wind_gust()
		self.totalRain = self.totalRain + self.weatherStation.get_current_rain_total()

		logger.debug('Rain Total               =\t{0:0.2f} mm'.format(self.totalRain))
		logger.debug('Wind Speed               =\t{0:0.2f} KMH'.format(self.currentWindSpeed))
		logger.debug('KMH wind_gust            =\t{0:0.2f} KMH'.format(self.currentWindGust))
  		logger.debug('Wind Direction           =\t{0:0.2f} Degrees'.format(self.weatherStation.current_wind_direction()))
		logger.debug('Wind Direction Voltage   =\t{0:0.3f} V'.format(self.weatherStation.current_wind_direction_voltage()))
		logger.debug('DS3231 Datetime          =\t{0}'.format(self.ds3231.read_datetime()))
		logger.debug('DS3231 Temperature       =\t{0:0.2f} C'.format(self.ds3231.getTemp()))
		logger.debug('BMP280 Temperature       =\t{0:0.2f} C'.format(self.bmp280.read_temperature())
		logger.debug('BMP280 Pressure          =\t{0:0.2f} KPa'.format(self.bmp280.read_pressure()/1000)
		logger.debug('BMP280 Altitude          =\t{0:0.2f} m'.format(self.bmp280.read_altitude())
    	logger.debug('BMP280 Sealevel Pressure =\t{0:0.2f} KPa'.format(self.bmp280.read_sealevel_pressure()/1000)
        luminosity = self.max44009.luminosity()
        logger.debug('MAX44009 Luminosity      =\t{0:0.2f} lux'.format(luminosity))
        logger.debug('MAX44009 Solar radiation =\t{0:0.2f} W/m^2'.format(luminosity*0.0079))
		outsideTemperature, outsideHumidity, crc_check = self.am2315.sense()
		logger.debug('AM2315 outTemperature    =\t{0:0.1f} C'.format(outsideTemperature))
		logger.debug('AM2315 outHumidity       =\t{0:0.1f} %%'.format(outsideHumidity))
		logger.debug('AM2315 crc               =\t{0}'.format(crc_check))

		Scroll_SSD1306.addLineOLED(display,  "Wind Speed=\t%0.2f KMH" % self.currentWindSpeed)
		Scroll_SSD1306.addLineOLED(display,  "Rain Total=\t%0.2f mm"  % self.totalRain)
		Scroll_SSD1306.addLineOLED(display,  "Wind Dir=%0.2f Degrees" % self.weatherStation.current_wind_direction())
		Scroll_SSD1306.addLineOLED(display,  "%s"                     % self.ds3231.read_datetime())

	def sampleWeather(self):
    	logger.info(" Weather Sampling") 
    	# get Weather Sensor data
    	currentWindSpeed = self.weatherStation.current_wind_speed()
    	currentWindGust = self.weatherStation.get_wind_gust()
    	self.totalRain = self.totalRain + self.weatherStation.get_current_rain_total()
    	self.currentWindDirection = self.weatherStation.current_wind_direction()
    	self.currentWindDirectionVoltage = self.weatherStation.current_wind_direction_voltage()
	
		# get BMP180 temperature and pressure
    	bmp180Temperature = self.mp280.read_temperature()
    	bmp180Pressure = self.bmp280.read_pressure()/1000
    	bmp180Altitude = self.bmp280.read_altitude()
    	bmp180SeaLevel = self.bmp280.read_sealevel_pressure()/1000
		
    	# get AM2315 Outside Humidity and Outside Temperature
    	outsideTemperature, outsideHumidity, crc_check = self.am2315.sense()

    	# get MAX44009 Luminosity
    	solarradiation = self.max44009.luminosity() * 0.0079
		
		self.addRainToArray(self.totalRain - self.lastRainReading)	
		self.rain60Minutes = self.totalRainArray()
		self.lastRainReading = self.totalRain
		logger.info("rain in past 60 minute= %s" % rain60Minutes)

    	logger.info("Sending Data to WeatherUnderground")
		if (WeatherUnderground_Enable):
			# build the URL
			myURL = "/weatherstation/updateweatherstation.php?"
			myURL += "ID="+WeatherUnderground_StationID
			myURL += "&PASSWORD="+WeatherUnderground_StationKey
			myURL += "&dateutc=now"

			# now weather station variables
			myURL += "&winddir=%i" % currentWindDirection
			myURL += "&windspeedmph=%0.2f" % (currentWindSpeed/1.6) 
			myURL += "&humidity=%i" % outsideHumidity
			myURL += "&tempf=%0.2f" % ((outsideTemperature*9.0/5.0)+32.0)
			myURL += "&rainin=%0.2f" % ((rain60Minutes)/25.4)
			myURL += "&baromin=%0.2f" % ((bmp180SeaLevel) * 0.2953)
			myURL += "&solarradiation=%0.2f" % solarradiation
			myURL += "&software=GroveWeatherPi"

			#send it
			conn = httplib.HTTPConnection("weatherstation.wunderground.com")
			conn.request("GET",myURL)
			res = conn.getresponse()
			log.debug(res.status + res.reason)
			textresponse = res.read()
			log.debug(textresponse)
			conn.close()

		if (MySQL_Enable):
			# now we have the data, stuff it in the database
			try:
				con = mdb.connect(MySQL_Url, MySQL_User, MySQL_Password, MySQL_Database);
				cur = con.cursor()
				query = 'INSERT INTO WeatherData(TimeStamp, currentWindSpeed, currentWindGust, totalRain, bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel, outsideTemperature, outsideHumidity, currentWindDirection, currentWindDirectionVoltage) VALUES(UTC_TIMESTAMP(), %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f, %.3f)' % (currentWindSpeed, currentWindGust, totalRain,  bmp180Temperature, bmp180Pressure, bmp180Altitude,  bmp180SeaLevel,  outsideTemperature, outsideHumidity, currentWindDirection, currentWindDirectionVoltage)
				cur.execute(query)
				con.commit()
			except mdb.Error, e:
				log.exception("MySQL Error",e)
				con.rollback()
			finally:    
				cur.close() 
				con.close()
				del cur
				del con


class GroveWeatherPiService(Service):
    def __init__(self, *args, **kwargs):
        super(GroveWeatherPiService, self).__init__(*args, **kwargs)
		weatherPi = GroveWeatherPi()

    def run(self):
    	log.info("GroveWeatherPi Program Started")
		secondCount = 1
        while not self.got_sigterm():
			# print every 10 seconds
			self.weatherPi.sampleAndDisplay()		

			# every 5 minutes, push data to mysql and check for shutdown
			if ((secondCount % (30)) == 0):
				self.weatherPi.sampleWeather()

			secondCount = secondCount + 1
			# reset secondCount to prevent overflow forever
			if (secondCount == 1000001):
				secondCount = 1	

			time.sleep(10.0)

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        sys.exit('Syntax: %s COMMAND' % sys.argv[0])

    cmd = sys.argv[1].lower()
    service = GrooveWeatherPiService('groove_weather_pi', pid_dir='/tmp')

    if cmd == 'start':
        service.start()
    elif cmd == 'stop':
        service.stop()
    elif cmd == 'status':
        if service.is_running():
            print "Service is running."
        else:
            print "Service is not running."
    else:
        sys.exit('Unknown command "%s".' % cmd)