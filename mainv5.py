## V4
## Goal - Clean up code.
## Add try/except/else to all areas

import RPi.GPIO as GPIO
from gpiozero import MotionSensor
import os, subprocess, time
import threading
from datetime import datetime
import sys
import dht
import numpy
import http.client, urllib
import MySQLdb
import paho.mqtt.client as mqtt
import Adafruit_DHT

#Globals
global end_Thread ## Used to end all Threads on exit
global zone

## Zone Setup

zone = 'living'

## Setup Vars

pirpin = 20 # Pin connected to PIR
end_Thread = 0 # Helps to end active threads

## Config Vars

active_timeout = 60 #Time between activity to determin if a zone is disconnected ( need to account for wifi lag)
avg_Time = 3 #Number of Temp Reads in array average
avg_Delay = 1 # Delay between temp readings
no_motion_delay = 900 ## Delay before motion timeout - 900 = 15min
screen_delay = 60 ## Delay off for the screen


#################
#Thread Classes
################

class Update_Data(threading.Thread):
    def __init__(self, delay, avg_Time, zone):
        threading.Thread.__init__(self)
        self.delay = delay
        self.avg_Time = avg_Time
        self.zone = zone
        
        self.mqtt() ## Connect for MQTT Updates
        
        self.DHT_SENSOR = Adafruit_DHT.DHT22
        self.DHT_PIN = 19
        
    def run(self):
        global end_Thread
        global startup
        
        zone = self.zone

        new_Temperature = "Calc." #sets initial value while being calculated.
        new_Humidity = 0
        
        startup = 1        
        
        ## Loop to set initial data for temp Average. Time of loop is based on avg_Time
        i = 0
        self.avg_temp_Data = []
        self.avg_humidity_Data = []
        
        log("Getting Average Temperature...Please Wait..")
        
        self.mq.publish("/tstat/living/temp", "Startup")
        
        while (i < self.avg_Time): # Fill array with valid data
            
            if self.pull_data():
                #Checks for valid results from pull_data if so advance loop
                i += 1
                time.sleep(self.delay)
                
            else:
            
                time.sleep(.1)
                        
        ## Calculate average Temp/Humidity          
        self.calc_avg()
        
        self.update()
        
        
        os.system('clear')
        
        log("Startup Complete")
        
        ### Start Forever loop to keep temp and humidity updated.
        try:
            startup = 0
            while (end_Thread == 0):
                if self.pull_data():
                    
                    del self.avg_temp_Data[0]
                    del self.avg_humidity_Data[0]
                    self.calc_avg()
                    
                    self.update()                                
               
                time.sleep(self.delay) # Sleep delay between readings, usually 1sec
            
        except (KeyboardInterrupt, SystemExit):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()
        GPIO.cleanup()
        menu.join()
    
    def pull_data(self):
     
        humidity, temperature = Adafruit_DHT.read_retry(self.DHT_SENSOR, self.DHT_PIN)
       
        if humidity is not None and temperature is not None:
    
            self.avg_humidity_Data.append(humidity)
            self.avg_temp_Data.append((temperature*(9/5)+32))
                
            return True
                
    def format(self, data):
        #Format value to 2 decimal plaees
        
        val = float("{0:.2f}".format(numpy.mean(data)))
        return val
        
    def calc_avg(self):
        self.avg_Temp = self.format(self.avg_temp_Data)
        self.avg_Humidity = self.format(self.avg_humidity_Data)
    
    def update(self):
    
        sql_update('temp', self.avg_Temp, self.zone, 'Update Temp Initial')
        sql_update('humidity', self.avg_Humidity, self.zone, 'Update Humidity Initial')
        self.mq.publish("/tstat/living/temp", self.avg_Temp)
        
    def mqtt(self):        
        self.mq = mqtt.Client()
        self.mq.connect("192.168.68.112")
        self.mq.loop_start()

class DB_Modify(threading.Thread):
    def __init__(self, zone):
        threading.Thread.__init__(self)
        self.zone = zone
    def run(self):
        global end_Thread
        global run_Temp
        global startup
        temp_Held = 0
        run_Temp = 60
        motion_Hold = 0
        zone = self.zone
        sql_update('relay', '0', zone, "Initial Setup - Clear Relay in DB") ##Old, control handles relay var

        while (end_Thread == 0):
            now = datetime.now()
            string_Time = now.strftime('%b-%d-%I:%M:%S')
            time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
            
            try:
                ##Get data from DB
                conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
                c = conn.cursor (MySQLdb.cursors.DictCursor)
                sql = ("SELECT * FROM settings WHERE zone = '" + self.zone + "'")
                c.execute(sql)
                row = c.fetchone()
                c.close()
                # Store Data from DB
                set_Temp = float(row['settemp'])
                backup_Temp = float(row['backuptemp'])
                hold_temp = int(row['holdtemp'])
                hold = int(row['hold'])
                temp = float(row['temp'])
                relay = float(row['relay'])
                motion = int(row['motion'])
                last_motion = int(row['lastmotion'])
                
            except:
                log("Error pulling data - DB Modify")
            
            if (hold == 1): ## If hold is ON
                
                if (temp_Held == 0): ## If hold was not on previous
                    temp_Held = 1 ## Set value so hold only triggers once
                    run_Temp = hold_Temp ## Set temp
                    log("Temp Held - Temp set to: " + str(run_Temp))
                    send_Notification("Living Room", ("Hold - Temp set to: " + str(run_Temp)))
                if (temp_Held == 1): ## If hold temp changes while on hold - maybe from gui
                    run_Temp = hold_Temp
                    
            if (hold == 0): ## If not holding
                
                if (temp_Held == 1): ## If temp was held
                    temp_Held = 0
                    if (motion == 1): ## If was holding and Motion
                        run_Temp = set_Temp
                        log(("Hold Removed - Returning Temp to " + str(run_Temp) + " Current Temp: " + str(temp)))
                        send_Notification("Living Room", ("Hold Removed - Temp set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                    if (motion == 0): ## If was holding and no motion
                        run_Temp = backup_Temp
                        motion_Hold = 1
                        log(("Hold Removed - No Motion - Set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                        send_Notification("Living Room", ("Hold Removed - No Motion - Temp set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                if (motion == 1):   ## Not Holding and IS Motion      
                    run_Temp = set_Temp
                    if (motion_Hold == 1): ## Motion notifications only trigger once
                        motion_Hold = 0
                        log("Motion Detected - Returning temp to " + str(run_Temp))
                        ##send_Notification("Living Room", ("Motion Detected, Temp returned to: " + str(run_Temp)))
                elif (motion == 0): ## Not holding and No Motion
                    run_Temp = backup_Temp
                    if (motion_Hold == 0):
                        motion_Hold = 1
                        log("Motion Held backup - temp is: " + str(backup_Temp))
                        ##send_Notification("Living Room", ("No Motion, Temp droped to: " + str(run_Temp)))
                        
            try:
                if (startup == 0): ## Only do Logic after initial temp average
                    ## Gives a .5 degree flux to avoid triggering heat on and off repeaditly if temp is close
                    ## Also only triggers if relay is off already to avoid constantly triggering
                    if (((float(temp) + .5) < float(run_Temp)) and (relay == 0)): 
                        try:
                            relay_On(zone)
                            log("Turned on Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Starting Relay")
                    elif ((float(temp) > float(run_Temp)) and (relay == 1)):
                        try:
                            relay_Off(zone)
                            log("Turned off Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Stopping Relay")
            except:
                log("Error in : DB Modify - Execution")
            
            time.sleep(.1)
class Detect_Motion(threading.Thread):
    def __init__(self, pin, motion_delay, screen_delay, zone):
        threading.Thread.__init__(self)
        self.pin = pin
        self.motion_delay = motion_delay
        self.zone = zone
        self.screen_delay = screen_delay
    def run(self):
        global end_Thread

        ## Setup Vars
        zone = self.zone
        last_motion = sql_fetch('lastmotion', zone)
        time_left = 0
        DB_motion = 1
        no_screen_delay = self.screen_delay
        no_motion_delay = self.motion_delay # 15 Min
        x = 0
        avg_Motion_data = []
        
        ## Setup PIR
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        pir=MotionSensor(self.pin)        
        
        while (x < 10): ## Get initial motion (sum of last 10 reads)
            if (pir.is_active == True):
                i = 1
            elif (pir.is_active == False):
                i = 0
            ## Add to array
            avg_Motion_data.append(i)
            time.sleep(1)
            x += 1
        
    
        while (end_Thread == 0): ## Start forever motion loop
            ## Get new motion and update total in array
            if (pir.is_active == True):
                i = 1
            elif (pir.is_active == False):
                i = 0
            avg_Motion_data.append(i)
            del avg_Motion_data[0]
            motion = sum(avg_Motion_data)

            time_now = time.time()

            ## Motion Detected

            if ((motion > 2)):
                ## Turn Display On when motion is detected.                    
                subprocess.call('xset dpms force on', shell=True)
                if ((motion > 5)):
                    DB_motion = 1                    
                    time_now = int(time.time())
                    motion_detect = 1
                    ## Update DB
                    sql_update('lastmotion', time_now, zone, 'Motion Detected - Update lastmotion')
                    sql_update('motion', DB_motion, zone, 'Motion Detected - Update motion') 
                    
                
            ### NO Motion
            if ((motion <= 2)):                   
            
                DB_motion = 0
                last_motion = sql_fetch('lastmotion', zone)
                avg_Motion_data.append(i)
                del avg_Motion_data[0]
                motion = sum(avg_Motion_data)
                time_now = int(time.time())
                time_left = ((last_motion + no_motion_delay) - time_now)
                if (time_now >= (last_motion + no_screen_delay)): ## Turn display off when no motion
                    subprocess.call('xset dpms force off', shell=True)
                if (time_now >= (last_motion + no_motion_delay)):
                    sql_update('motion', DB_motion, zone, 'No Motion - Update motion')
                    
            time.sleep(.1)
               
    GPIO.cleanup()
class Activity(threading.Thread):
    def __init__(self, active_timout):
        threading.Thread.__init__(self)
        self.active_timeout = active_timeout
    def run(self):
        ## Work in progress
        ## Set vars for actifity monitor
        global end_Thread
        kitchen_notify = 0
        control_notify = 0
        kitchen_update = 0
        control_update = 0
        upstairs_update = 0
        upstairs_notify = 0
        try:
            while (end_Thread == 0):
                time.sleep(1)
                now = float(time.time())
                ## Update Activity for Living
                sql_update("last_updated", now, "living", "Update for Activity")
                ## Pull Activity from other zones
                kitchen_activity = float(sql_fetch("last_updated", "kitchen"))
                control_activity = float(sql_fetch("last_updated", "control"))
                upstairs_activity = float(sql_fetch("last_updated", "upstairs"))

                ## Kitchen Activity Monitor
                if (now > (kitchen_activity + self.active_timeout)): #No Activity
                    sql_update("active", '0', "kitchen", "Kitchen Activity")
                    if (kitchen_notify == 0): #Not Notified
                        try:
                            send_Notification("Living Room", "System - Kitchen Zone Offline")
                        except:
                            log("Error in Activity Monitor")
                        else:
                            kitchen_notify = 1
                        
                if(now < (kitchen_activity + self.active_timeout)): # Activity
                    sql_update("active", '1', "kitchen", "Kitchen Activity")
                    if(kitchen_notify == 1):
                        try:
                            send_Notification("Living Room", "System - Kitchen Zone ReConnected")
                        except:
                            log("Error in Activity Monitor")
                        else:
                            kitchen_notify = 0
                                
                ## Control Activity Monitor
                if (now > (control_activity + self.active_timeout)): #No Activity
                    sql_update("active", '0', "control", "Control Activity")
                    if (control_notify == 0): #Not Notified
                        send_Notification("Living Room", "System - Relay Control Offline") 
                        control_notify = 1
                        
                if(now < (control_activity + self.active_timeout)): # Activity
                    sql_update("active", '1', "control", "Control Activity")
                    if(control_notify == 1):
                        send_Notification("Living Room", "System - Relay Control ReConnected")
                        control_notify = 0

                ## Upstairs Activity Monitor
                if (now > (upstairs_activity + self.active_timeout)): #No Activity
                    sql_update("active", '0', "upstairs", "Upstairs Activity")
                    if (upstairs_notify == 0): #Not Notified
                        send_Notification("Living Room", "System - Upstairs Zone Offline") 
                        upstairs_notify = 1
                        
                if(now < (upstairs_activity + self.active_timeout)): # Activity
                    sql_update("active", '1', "upstairs", "Upstairs Activity")
                    if(upstairs_notify == 1):
                        send_Notification("Living Room", "System - Upstairs ReConnected")
                        upstairs_notify = 0
        except:
            log("Error in Activity Function")



####################
## Functions
####################

def relay_On(zone):
    relay_State = int(sql_fetch('relay', zone))
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    try:
        #GPIO.output(pin, GPIO.HIGH)
        relay_State = 1
    except:
        log('Error turning ON relay')
    sql_update('relay', relay_State, zone, 'relay_On')
    

def relay_Off(zone):
    relay_State = int(sql_fetch('relay', zone))
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    relay_State = 0
    try:
        #GPIO.output(pin, GPIO.LOW)
        
        sql_update('relay', relay_State, zone, 'relay_Off')
    except:
        log("Database Error in Relay Off")
        relay = 1
        

def send_Notification(title, body):
    try:
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
          urllib.parse.urlencode({
                "token": "awmq2qh4qoijvztozwuvte5qdbikhm",
                "user": "u9yffbyi7ppxhcw79xwfwg5afhszk2",
                "message": body,
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()
    except:
        error = ("Error Sending Notification - " + str(body))
        log(error)
def log(message):
    now = datetime.now()
    string_Time = now.strftime('%b-%d-%I:%M:%S')
    log_Info = str("\n" + string_Time + " - " + str(message))
    print(log_Info)
def screen_print(zone):
    try:
        temp = float(sql_fetch('temp', zone))
        hold = int(sql_fetch('hold', zone))
        motion = int(sql_fetch('motion', zone))
        relay = int(sql_fetch('relay', zone))
    except:
        log("Error pulling data - DB Modify")
    global run_Temp
    now = datetime.now()
    string_Time = now.strftime('%b-%d-%I:%M:%S')
    string_Info = str("\n" + string_Time)
    if (relay == 1):
        string_Info = str(string_Info + " - Relay ON  - ")
    if (relay == 0):
        string_Info = str(string_Info + " - Relay OFF  - ")
    string_Info = str(string_Info + "Current Temp is: " + str(temp) + "F" + " - Thermostat is set at: " + str(run_Temp))
    if (hold == 1):
        string_Info = str(string_Info + " - Temp HELD")
    return string_Info

    print(string_Info)
def sql_update(field, value, zone, msg):
    ## Connect to SQL DB
    try:
        conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)
    except:
        log("Error Connecting to DB")
    else:
        ## Create SQL and Update settings table
        try:
            sql = ("UPDATE settings SET " + str(field) + " = '" + str(value) + "' WHERE zone = '" + str(zone) + "'")
            c.execute(sql)
            conn.commit()
            #log(("Changed " + str(field) + " to " + str(value) + " for zone " + str(zone)))
        except:
            error = ("Error in SQL Update - " + msg)
            log(error)
        
def sql_fetch(field, zone):
    ## Connect to SQL DB
    try:
        conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)
        sql = ("SELECT " + str(field) + " FROM settings WHERE zone = '" + str(zone) + "'")
        c.execute(sql)
        row = c.fetchone()
        return(row[field])
    except:
        error = ("Error in SQL Update - ")
        log(error)
        

###############################
## Here to start thread for temp/humidity monitoring
###############################

try:
    Data = Update_Data(avg_Delay, avg_Time, zone)
    Data.start()
except:
    log ("Error Starting Temp Update")

try:
    DB = DB_Modify(zone)
    DB.start()
except:
    log("Error Starting DB Update")
try:
    AM = Activity(active_timeout)
    AM.start()
except:
    log("Error Starting Activity Monitor")
    
#################################
##Start Motion Detection
#################################

try:
    motion = Detect_Motion(pirpin, no_motion_delay, screen_delay, zone)
    motion.start()
except:
    log("Error Starting Motion Detection")
    
##########################
## Main Loop
##########################
## System Startup Notification
send_Notification("Living Room", "Living - System Started")
try:
    while (end_Thread == 0):
        time.sleep(1)


#### Set vars for actifity monitor
##kitchen_notify = 0
##control_notify = 0
##kitchen_update = 0
##control_update = 0
##upstairs_update = 0
##upstairs_notify = 0
##try:
##    while (end_Thread == 0):
##        time.sleep(1)
##        now = float(time.time())
##        sql_update("last_updated", now, "living", "Update for Activity")
##        kitchen_activity = float(sql_fetch("last_updated", "kitchen"))
##        control_activity = float(sql_fetch("last_updated", "control"))
##        upstairs_activity = float(sql_fetch("last_updated", "upstairs"))
##
##        ##Kitchen Zone Activity Monitor
##        if (now > (kitchen_activity + active_timeout)): #No Activity
##            sql_update("active", '0', "kitchen", "Kitchen Activity")
##            if (kitchen_notify == 0): #Not Notified
##                send_Notification("Living Room", "System - Kitchen Zone Offline")
##                kitchen_notify = 1
##                
##        if(now < (kitchen_activity + active_timeout)): # Activity
##            sql_update("active", '1', "kitchen", "Kitchen Activity")
##            if(kitchen_notify == 1):
##                send_Notification("Living Room", "System - Kitchen Zone ReConnected")
##                kitchen_notify = 0
##                
##                
##        ## Control Activity Monitor
##        if (now > (control_activity + active_timeout)): #No Activity
##            sql_update("active", '0', "control", "Control Activity")
##            if (control_notify == 0): #Not Notified
##                send_Notification("Living Room", "System - Relay Control Offline") 
##                control_notify = 1
##                
##        if(now < (control_activity + active_timeout)): # Activity
##            sql_update("active", '1', "control", "Control Activity")
##            if(control_notify == 1):
##                send_Notification("Living Room", "System - Relay Control ReConnected")
##                control_notify = 0
##
##        ## Upstairs Activity Monitor
##        if (now > (upstairs_activity + active_timeout)): #No Activity
##            sql_update("active", '0', "upstairs", "Upstairs Activity")
##            if (upstairs_notify == 0): #Not Notified
##                send_Notification("Living Room", "System - Upstairs Zone Offline") 
##                upstairs_notify = 1
##                
##        if(now < (upstairs_activity + active_timeout)): # Activity
##            sql_update("active", '1', "upstairs", "Upstairs Activity")
##            if(upstairs_notify == 1):
##                send_Notification("Living Room", "System - Upstairs ReConnected")
##                upstairs_notify = 0
  

except (KeyboardInterrupt, SystemExit):
    send_Notification("Living Room", "Living - App Closing")
    end_Thread = 1
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
log("Exiting...")
GPIO.cleanup()
DB.join()
motion.join()
Data.join()

sys.exit()
