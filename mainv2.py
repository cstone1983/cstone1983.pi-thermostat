import RPi.GPIO as GPIO
from gpiozero import MotionSensor
import time
import threading
from datetime import datetime
import sys
import dht
import numpy
import os
import lcddriver
import http.client, urllib
import MySQLdb

#Globals
global relaypin
global pirpin
global new_Temperature
global new_Humidity
global relay_State
global hold_Temp
global string_Time
global string_Info
global end_Thread
global zone

## Setup Vars

zone = 'living'
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


## Setup GPIO
#GPIO.setmode(GPIO.BCM) # Board Setup
#GPIO.setwarnings(False)


#################
#Thread Classes
#################

class Update_Data(threading.Thread):
    def __init__(self, delay, avg_Time):
        threading.Thread.__init__(self)
        self.delay = delay
        self.avg_Time = avg_Time

    def run(self):
        global new_Temperature
        global new_Humidity
        global end_Thread
        global zone

        #### SQlite connection
        conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)

        new_Temperature = "Calc." #sets initial value while being calculated.
        new_Humidity = 0
        old_Temperature = 0
        instance = dht.DHT11(pin=19)
        
        ## Loop to set initial data for temp Average. Time of loop is based on avg_Time
        i = 0
        avg_temp_Data = []
        avg_humidity_Data = []
        print("\nGetting Average Temperature...Please Wait..")
        while (i < self.avg_Time):
            result = instance.read() # Get sensor data from dht.py
            if result.is_valid():
                get_Temp = result.temperature # move result to local var
                get_Temp = (get_Temp*(9/5)+32) # convert to F - Will move to dht.py eventually
                get_Humidity = result.humidity
                avg_humidity_Data.append(get_Humidity)
                if (int(get_Temp) > 32): #Eliminate values under 32, most common errors were 32 and 0
                    avg_temp_Data.append(get_Temp)
                    #print(str((self.avg_Time - i)) + " Temp: " + str(get_Temp) + " Humidity: " + str(get_Humidity)) # Debugging print, end will proball show just dots or just countdown
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
                        try:
                            sql = """UPDATE settings SET temp = %s WHERE zone = %s"""
                            val = (new_Temperature, zone)
                            c.execute(sql, val)
                            conn.commit()
                        except:
                            print("Database Error in Temp Data Update")
                       
                ## Get current Humidity

                current_Humidity = result.humidity
                if (current_Humidity != False):
                    avg_humidity_Data.append(current_Humidity)
                    del avg_humidity_Data[0]
                    new_Humidity = float("{0:2f}".format(numpy.mean(avg_humidity_Data)))
                    new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data)))
                    try:
                        sql = """UPDATE settings SET humidity = %s WHERE zone = %s"""
                        val = (new_Humidity, zone)
                        c.execute(sql, val)
                        conn.commit()
                        
                    except:
                            print("Database Error in Humidity Data Update")
                            
                time.sleep(self.delay) # Sleep delay between readings, usually 1sec
            
        except (KeyboardInterrupt, SystemExit):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()
        GPIO.cleanup()
        menu.join()

class DB_Modify(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global set_Temp
        global run_Temp
        global backup_Temp
        global end_Thread
        global hold_Temp
        global temp_overriden
        global last_motion
        global DB_Change
        global relay_State
        temp_Held = 0
        run_Temp = 50
        motion_Hold = 0
        relaypin = 23 # Pin connected to relay
        try:
            conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
            c = conn.cursor (MySQLdb.cursors.DictCursor)
        except:
            print("Error connecting to db")
        try:
            relay_State = 0
            sql = "UPDATE settings SET relay = '0' WHERE zone = 'living'"
            val = (relay_State, zone)
            c.execute(sql)
            conn.commit()
        except:
            log("DB Modify - Error setting initial relay state")
        while (end_Thread == 0):
            try:
                conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
                c = conn.cursor (MySQLdb.cursors.DictCursor)
            except:
                print("Error connecting to db")
            now = datetime.now()
            string_Time = now.strftime('%b-%d-%I:%M:%S')
            time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
            
            try:
                c.execute("SELECT temp, backuptemp, holdtemp, hold, lastmotion, motion, settemp, relay FROM settings WHERE zone = 'living'")
                row = c.fetchone()
                temp = float(row["temp"])
                backup_Temp = float(row["backuptemp"])
                hold_Temp = float(row["holdtemp"])
                hold = int(row["hold"])
                last_motion = int(row["lastmotion"])
                motion = int(row["motion"])
                set_Temp = float(row["settemp"])
                relay = int(row["relay"])
            except:
                print("Error pulling data - DB Modify")
                  
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
                        log(("Hold Removed - Returning Temp to " + str(run_Temp)))
                        send_Notification("Living Room", ("Hold Removed - Temp set to: " + str(run_Temp)))
                    if (motion == 0):
                        run_Temp = backup_Temp
                        motion_Hold = 1
                        log(("Hold Removed - No Motion - Set to: " + str(run_Temp)))
                        send_Notification("Living Room", ("Hold Removed - No Motion - Temp set to: " + str(run_Temp)))
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
                            relay_On(relaypin)
                            log("Turned on Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Starting Relay")
                    elif ((float(temp) > float(run_Temp)) and (relay == 1)):
                        try:
                            relay_Off(relaypin)
                            log("Turned off Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Stopping Relay")
            except:
                log("Error in : DB Modify - Execution")
            
            time.sleep(1)
class Detect_Motion(threading.Thread):
    def __init__(self, pin, delay):
        threading.Thread.__init__(self)
        self.pin = pin
        self.delay = delay
    def run(self):
        global time_left
        global end_Thread
        global string_Time
        global temp_overriden
        global last_motion
        #### SQlite connection
        conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)


        time_left = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        #GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pir=MotionSensor(self.pin)        
        DB_motion = 1
        no_motion_delay = 900 # 15 Min
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
                    #print("motion")
                    DB_motion = 1
                    time_now = int(time.time())
                    try:
                        sql = """UPDATE settings SET lastmotion = %s WHERE zone = %s"""
                        val = (time_now, zone)
                        last_motion = time_now
                        c.execute(sql, val)
                        conn.commit()
                        try:
                            sql = """UPDATE settings SET motion = %s WHERE zone = %s"""
                            val = (DB_motion, zone)
                            c.execute(sql, val)
                            conn.commit()
                        except:
                              print("Database Error in Motion Update motion = 1") 
                    except:
                        print("Database Error in Motion Update last motion")
                        
                    motion_detect = 1
                    
                ### NO Motion
                elif ((motion <= 5)):
                    #print("No Moion")                    
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
                            try:
                                DB_motion = 0
                                sql = """UPDATE settings SET motion = %s WHERE zone = %s"""
                                val = (DB_motion, zone)
                                c.execute(sql, val)
                                conn.commit()
                            except:
                                print("Database Error in Motion Update no motion")
                        time.sleep(.2)
                    
                

               
                    
                time.sleep(.2)
        except(KeyboardInterrupt, SystemExit):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()        
    GPIO.cleanup()
class Menu_System(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global set_Temp
        global new_Temperature
        global backup_Temp
        global time_left
        global string_Time
        global hold_Temp
        global end_Thread
        global avg_temp_Data
        global avg_humidity_Data
        global DB_Change
        global zone
        screen_print()
        conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)
        time.sleep(2)
        while (end_Thread == 0):
            print(screen_print())
            action = input("\nWhat do you want to do: ")

            if (action == "temp"):
                do_this = input("What Temperature do you want to change to: ")
                try:
                    if (float(do_this) > 50 and float(do_this) < 80):
                        set_Temp = float(do_this)
                        print("Temp Changed to: " + str(set_Temp))
                        sql = ("UPDATE settings set settemp = %s WHERE zone = %s""")
                        val = (do_this, zone)
                        c.execute(sql, val)
                        conn.commit()
                        DB_Change = 1
                    else:
                        print("Not a valid Temp")
                except:
                    print("Invalid entry")
            elif (action == "help"):
                print("\n------------------")
                print("temp - Change Set Temperature")
                print("data - Show Current Average Data Set")
                print("backup temp - Set Backup Temp for No Motion aka Night")
                print("motion - Time left before motion timeout")
                print("exit - exit thermostat")
            elif (action == "info"):
                print(screen_print())
            elif (action == "backup temp"):
                do_this = input("Change Backup Temp to: ")
                try:
                    sql = """UPDATE settings SET backuptemp = %s WHERE zone = %s"""
                    val = (do_this, zone)
                    c.execute(sql, val)
                    conn.commit()
                except:
                    print("DB Error in DB_Modify")
            elif (action == "motion"):
                time_left_min = int(time_left / 60)
                time_left_sec = time_left - (time_left_min * 60)
                print("Time left untill motion timeout is: " + str(time_left_min) + " Minutes and " + str(time_left_sec) + " seconds")

            elif (action == "data"):
                print(avg_temp_Data)
                print("\n" + str(avg_humidity_Data))

            elif (action == "exit"):
                send_Notification("Living Room", "Thermostat App Closing")
                end_Thread = 1
        
            action = 0
        GPIO.cleanup()
####################
## Functions
####################

def relay_On(pin):
    global relay_State
    global zone
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)

    GPIO.output(pin, GPIO.HIGH)
    zone = 'living'
    relay_State = 1
    try:
        sql = ("UPDATE settings SET relay = %s WHERE zone = %s")
        val = (relay_State, zone)
        c.execute(sql, val)
        conn.commit()
    except:
        print("Database Error in Relay ON")
    

def relay_Off(pin):
    global relay_State
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    try:
        GPIO.output(pin, GPIO.LOW)
        relay = 0
        try:
            relay = 0
            zone = 'living'
            sql = ("UPDATE settings SET relay = %s WHERE zone = %s")
            val = (relay, zone)
            c.execute(sql, val)
            conn.commit()
        except:
            print("Database Error in Relay Off")
            
    except:
        print("Error Stopping Relay")
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
def screen_print():
    global relay_State
    global run_Temp
    now = datetime.now()
    string_Time = now.strftime('%b-%d-%I:%M:%S')
    if (relay_State == 1):
            string_Info = str("\n" + string_Time + " - Relay ON  - " + "Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(run_Temp))
            
    elif (relay_State == 0):

            string_Info = str("\n" + string_Time + " - Relay OFF - " + "Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(run_Temp))
    return string_Info

    print(string_Info)

###############################
## Here to start thread for temp/humidity monitoring
###############################
try:
    Data = Update_Data(avg_Delay, avg_Time)
    Data.start()
except:
    print ("Error Starting Temp Update")

try:
    DB = DB_Modify()
    DB.start()
except:
    print("Error Starting DB Update")

    
###########
# Start User Input
####################
try:

    menu = Menu_System()
    menu.start()
except:
    print("Error Starting User Input")

    
#################################
##Start Motion Detection
#################################
try:
    motion = Detect_Motion(pirpin, 900)
    motion.start()
except:
    print("Error Starting Motion Detection")
    
##########################
## Main Loop
##########################

try:
    while (end_Thread == 0):
        time.sleep(1)        
##        now = datetime.now()
##        string_Time = now.strftime('%b-%d-%I:%M:%S')
##        
##        
##
##        time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
##        
##        if (new_Temperature != "Calc."):
##            if (( (float(new_Temperature) + .5) < float(set_Temp)) and (relay_State == 0)):
##                try:
##                    relay_On(relaypin)
##                    print(screen_print())
##                    #send_Notification("Living Room", ("Heater is -ON- and the Temp is: " + str(new_Temperature)))
##                    
##                except:
##                    print("\nError Starting Relay")
##            elif ((float(new_Temperature) > float(set_Temp)) and (relay_State == 1)):
##                try:
##                    relay_Off(relaypin)
##                    #send_Notification("Living Room", ("Heater is -OFF- and Temp is: " + str(new_Temperature)))
##                    print(screen_print())
##                except:
##                    print("\nError Stopping Relay")
##                    
##        time.sleep(.1)
        
except (KeyboardInterrupt, SystemExit):
    send_Notification("Living Room", "Thermostat App Closing")
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
print("Exiting...")
GPIO.cleanup()
DB.join()
motion.join()
Data.join()

sys.exit()
