## V 2.1
## Goal - Clean up code.
## Remove excess vars
#### move sql updates to function ( pass field, value, zone)
## Make threads independent, no globals as possible
#### replace prints with log


import RPi.GPIO as GPIO
from gpiozero import MotionSensor
import time
import threading
from datetime import datetime
import sys
import dht
import numpy
import os
import http.client, urllib
import MySQLdb

#Globals
global relaypin
global end_Thread
global zone

## Zone Setup

zones = ['living']

## Setup Vars
now = datetime.now()
string_Time = now.strftime('%b-%d-%I:%M:%S')
new_Temperature = 0
new_Humidity = 0
relay_State = 0 # State of relay, so relay is not constantly being triggered on or off

#Pin Numbers, Temp Sensor set in dht.py, lcd pins set in lcddriver
pirpin = 20 # Pin connected to PIR

avg_Time = 30 #Number of Temp Reads in array average
avg_Delay = 1 # Delay between temp readings
hold_Temp = 0 #used to hold temp from user input
end_Thread = 0 # Helps to end active threads
no_motion_delay = 900 ## Delay before motion timeout - 900 = 15min

#################
#Thread Classes
#################

class Update_Data(threading.Thread):
    def __init__(self, delay, avg_Time, zone):
        threading.Thread.__init__(self)
        self.delay = delay
        self.avg_Time = avg_Time
        self.zone = zone

    def run(self):
        global end_Thread
        zone = self.zone

        new_Temperature = "Calc." #sets initial value while being calculated.
        new_Humidity = 0
        old_Temperature = 0
        instance = dht.DHT11(pin=19)
        
        ## Loop to set initial data for temp Average. Time of loop is based on avg_Time
        i = 0
        avg_temp_Data = []
        avg_humidity_Data = []
        log("Getting Average Temperature...Please Wait..")
        while (i < self.avg_Time):
            result = instance.read() # Get sensor data from dht.py
            if result.is_valid():
                get_Temp = result.temperature # move result to local var
                get_Temp = (get_Temp*(9/5)+32) # convert to F - Will move to dht.py eventually
                get_Humidity = result.humidity
                avg_humidity_Data.append(get_Humidity)
                if (int(get_Temp) > 32): #Eliminate values under 32, most common errors were 32 and 0
                    avg_temp_Data.append(get_Temp)
                    #log(str((self.avg_Time - i)) + " Temp: " + str(get_Temp) + " Humidity: " + str(get_Humidity)) # Debugging print, end will proball show just dots or just countdown
                    i += 1
                    time.sleep(self.delay)
                    
        ## Calculate average Temp/Humidity          
        new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data))) # Do initial Average
        new_Humidity = float("{0:.2f}".format(numpy.mean(avg_humidity_Data)))

        os.system('clear')
        log("Done Getting Temp")
        
        ### Start Forever loop to keep temp and humidity updated.
        try:
            while (end_Thread == 0):
                result = instance.read()
                if result.is_valid():
                    current_Temp = result.temperature #Pull current temp
                    current_Temp = (current_Temp*(9/5)+32) ## Convert to F
                    if (int(current_Temp > 32)):
                        avg_temp_Data.append(current_Temp)
                        del avg_temp_Data[0]
                        new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data)))
                        ## Update Database
                        sql_update('temp', new_Temperature, zone, 'Update Temp')
                       
                ## Get current Humidity

                current_Humidity = result.humidity
                if (current_Humidity != False):
                    avg_humidity_Data.append(current_Humidity)
                    del avg_humidity_Data[0]
                    new_Humidity = float("{0:2f}".format(numpy.mean(avg_humidity_Data)))
                    new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data)))
                    ## Update Database
                    sql_update('humidity', new_Humidity, zone, 'Update Humidity')
                            
                time.sleep(self.delay) # Sleep delay between readings, usually 1sec
            
        except (KeyboardInterrupt, SystemExit):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()
        GPIO.cleanup()
        menu.join()

class DB_Modify(threading.Thread):
    def __init__(self, zone):
        threading.Thread.__init__(self)
        self.zone = zone
    def run(self):
        global end_Thread
        global run_Temp        
        temp_Held = 0
        run_Temp = 60
        motion_Hold = 0
        relaypin = 23 # Pin connected to relay
        zone = self.zone
        sql_update('relay', '0', zone, "Initial Setup - Clear Relay in DB")

        while (end_Thread == 0):
            now = datetime.now()
            string_Time = now.strftime('%b-%d-%I:%M:%S')
            time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
            
            try:
                temp = float(sql_fetch('temp', zone))
                backup_Temp = float(sql_fetch('backuptemp', zone))
                hold_Temp = float(sql_fetch('holdtemp', zone))
                hold = int(sql_fetch('hold', zone))
                last_motion = int(sql_fetch('lastmotion', zone))
                motion = int(sql_fetch('motion', zone))
                set_Temp = float(sql_fetch('settemp', zone))
                relay = int(sql_fetch('relay', zone))
            except:
                log("Error pulling data - DB Modify")
            
            if (hold == 1):
                
                if (temp_Held == 0):
                    temp_Held = 1
                    run_Temp = hold_Temp
                    log("Temp Held - Temp set to: " + str(run_Temp))
                    send_Notification("Living Room", ("Hold - Temp set to: " + str(run_Temp)))
                if (temp_Held == 1): ## Update hold temp while it is being held.
                    run_Temp = hold_Temp
                    
            if (hold == 0):
                
                if (temp_Held == 1): ## If temp was held
                    temp_Held = 0
                    if (motion == 1):
                        run_Temp = set_Temp
                        log(("Hold Removed - Returning Temp to " + str(run_Temp) + " Current Temp: " + str(temp)))
                        send_Notification("Living Room", ("Hold Removed - Temp set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                    if (motion == 0):
                        run_Temp = backup_Temp
                        motion_Hold = 1
                        log(("Hold Removed - No Motion - Set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                        send_Notification("Living Room", ("Hold Removed - No Motion - Temp set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                if (motion == 1):                    
                    run_Temp = set_Temp
                    if (motion_Hold == 1):
                        motion_Hold = 0
                        log("Motion Detected - Returning temp to " + str(run_Temp))
                        send_Notification("Living Room", ("Motion Detected, Temp returned to: " + str(run_Temp)))
                elif (motion == 0):
                    run_Temp = backup_Temp
                    if (motion_Hold == 0):
                        motion_Hold = 1
                        log("Motion Held backup - temp is: " + str(backup_Temp))
                        send_Notification("Living Room", ("No Motion, Temp droped to: " + str(run_Temp)))
                        
            try:
                if (new_Temperature != "Calc."):
                    if (((float(temp) + .5) < float(run_Temp)) and (relay == 0)):
                        try:
                            relay_On(relaypin, zone)
                            log("Turned on Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Starting Relay")
                    elif ((float(temp) > float(run_Temp)) and (relay == 1)):
                        try:
                            relay_Off(relaypin, zone)
                            log("Turned off Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Stopping Relay")
            except:
                log("Error in : DB Modify - Execution")
            
            time.sleep(.2)
class Detect_Motion(threading.Thread):
    def __init__(self, pin, delay, zone):
        threading.Thread.__init__(self)
        self.pin = pin
        self.delay = delay
        self.zone = zone
    def run(self):
        global end_Thread
        zone = self.zone
        last_motion = sql_fetch('lastmotion', zone)
        time_left = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        #GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pir=MotionSensor(self.pin)        
        DB_motion = 1
        no_motion_delay = self.delay # 15 Min
        temp_overriden = 0 #used so set_temp only gets changed once
        x = 0
        avg_Motion_data = []
        while (x < 10):
            
            if (pir.is_active == True):
                i = 1
            elif (pir.is_active == False):
                i = 0
            
            #i = GPIO.input(self.pin)
            avg_Motion_data.append(i)
            time.sleep(1)
            x += 1

        try:
            while (end_Thread == 0):
                #pir=MotionSensor(self.pin)
                GPIO.setmode(GPIO.BCM)
                #i = GPIO.input(self.pin)
                if (pir.is_active == True):
                    i = 1
                elif (pir.is_active == False):
                    i = 0
                
                avg_Motion_data.append(i)
                del avg_Motion_data[0]
                motion = sum(avg_Motion_data)
                time_now = time.time()

                ## Motion Detected
                if ((motion > 5)):
                    #log("motion")
                    DB_motion = 1
                    time_now = int(time.time())
                    sql_update('lastmotion', time_now, zone, 'Motion Detected - Update lastmotion')
                    sql_update('motion', DB_motion, zone, 'Motion Detected - Update motion')
                        
                    motion_detect = 1
                    
                ### NO Motion
                elif ((motion <= 5)):
                    #log("No Moion")                    
                    while ((motion < 5)):
                        if (pir.is_active == True):
                            i = 1
                        elif (pir.is_active == False):
                            i = 0
                        
                        avg_Motion_data.append(i)
                        del avg_Motion_data[0]
                        motion = sum(avg_Motion_data)
                        time_now = int(time.time())
                        time_left = ((last_motion + no_motion_delay) - time_now)
                        if (time_now >= (last_motion + no_motion_delay)) and (DB_motion == 1):
                            sql_update('motion', DB_motion, zone, 'No Motion - Update motion')
                            
                        time.sleep(.2)
                    
                

               
                    
                time.sleep(.2)
        except(KeyboardInterrupt, SystemExit):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()        
    GPIO.cleanup()
class Menu_System(threading.Thread):
    def __init__(self, zone):
        threading.Thread.__init__(self)
        self.zone = zone
    def run(self):
        global end_Thread
        zone = self.zone
        last_motion = int(sql_fetch('lastmotion', zone))
        screen_print(zone)
        while (end_Thread == 0):
            time.sleep(.5)
            print(screen_print(zone))
            action = input("\nWhat do you want to do: ")

            if (action == "temp"):
                do_this = input("What Temperature do you want to change to: ")
                try:
                    if (float(do_this) > 49 and float(do_this) < 81):
                        sql_update('settemp', do_this, zone, 'Menu - Update settemp')
                        log("Temp Changed to: " + str(do_this))
                    else:
                        log("Not a valid Temp")
                except:
                    print("Invalid entry - Must be between 50 and 80")
            elif (action == "help"):
                print("\n------------------")
                print("temp - Change Set Temperature")
                print("backup temp - Set Backup Temp for No Motion aka Night")
                print("exit - exit thermostat")
            elif (action == "backup temp"):
                do_this = input("Change Backup Temp to: ")
                sql_update('backuptemp', do_this, zone, "Menu - Update backuptemp")
                
            elif (action == "exit"):
                send_Notification("Living Room", "Thermostat App Closing")
                end_Thread = 1
        
            action = 0
        GPIO.cleanup()
####################
## Functions
####################

def relay_On(pin, zone):
    relay_State = int(sql_fetch('relay', zone))
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    try:
        GPIO.output(pin, GPIO.HIGH)
        relay_State = 1
    except:
        log('Error turning ON relay')
    sql_update('relay', relay_State, zone, 'relay_On')
    

def relay_Off(pin, zone):
    relay_State = int(sql_fetch('relay', zone))
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    relay_State = 0
    try:
        GPIO.output(pin, GPIO.LOW)
        
        sql_update('relay', relay_State, zone, 'relay_Off')
    except:
        log("Database Error in Relay Off")
        relay = 1
        

def send_Notification(title, body):
   
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
            "token": "awmq2qh4qoijvztozwuvte5qdbikhm",
            "user": "u9yffbyi7ppxhcw79xwfwg5afhszk2",
            "message": body,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
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
        log("error")

###############################
## Here to start thread for temp/humidity monitoring
###############################
for x in zones:
    try:
        Data = Update_Data(avg_Delay, avg_Time, x)
        Data.start()
    except:
        log ("Error Starting Temp Update")

    try:
        DB = DB_Modify(x)
        DB.start()
    except:
        log("Error Starting DB Update")

    
###########
# Start User Input
####################
for x in zones:
    try:

        menu = Menu_System(x)
        menu.start()
    except:
        log("Error Starting User Input")

    
#################################
##Start Motion Detection
#################################
for x in zones:
    try:
        motion = Detect_Motion(pirpin, no_motion_delay, x)
        motion.start()
    except:
        log("Error Starting Motion Detection")
    
##########################
## Main Loop
##########################

try:
    while (end_Thread == 0):
        time.sleep(1)        

except (KeyboardInterrupt, SystemExit):
    send_Notification("Living Room", "Thermostat App Closing")
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
log("Exiting...")
GPIO.cleanup()
DB.join()
motion.join()
Data.join()

sys.exit()
