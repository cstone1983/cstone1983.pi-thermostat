import os, subprocess, time
import threading
from datetime import datetime
import sys
import Adafruit_DHT
import numpy
import http.client, urllib
import MySQLdb
import paho.mqtt.client as mqtt

#Globals
global relaypin
global end_Thread
global zone

## Zone Setup

zone = 'upstairs'

## Setup Vars
now = datetime.now()
string_Time = now.strftime('%b-%d-%I:%M:%S')
new_Temperature = 0
new_Humidity = 0
relay_State = 0 # State of relay, so relay is not constantly being triggered on or off
avg_Time = 5 #Number of Temp Reads in array average
avg_Delay = 2 # Delay between temp readings
hold_Temp = 0 #used to hold temp from user input
end_Thread = 0 # Helps to end active threads


#################
#Thread Classes
#################

class Update_Data(threading.Thread):
    def __init__(self, delay, avg_Time, zone):
        threading.Thread.__init__(self)
        self.delay = delay
        self.avg_Time = avg_Time
        self.zone = zone
        
        self.mq = mqtt.Client()
        self.mq.connect("192.168.68.112")
        self.mq.loop_start()

    def run(self):
        global end_Thread
        global startup
        
        ## Set Vars
        #Sensor Vars
        sensor = Adafruit_DHT.DHT22
        pin = 2
        #Setup Values
        new_Temperature = "Calc." #sets initial value while being calculated.
        new_Humidity = 0
        old_Temperature = 0
        #Sets var for initial startup
        startup = 1        

        ## Loop to set initial data for temp Average. Time of loop is based on avg_Time
        i = 0
        avg_temp_Data = []
        avg_humidity_Data = []
        log("Getting Average Temperature...Please Wait..")
        
        while (i < self.avg_Time):
            humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)# Get sensor data from dht.py
            if humidity is not None and temperature is not None:
                get_Temp = (temperature*(9/5)+32) # convert to F - Will move to dht.py eventually
                avg_humidity_Data.append(humidity)
                avg_temp_Data.append(get_Temp)
                i += 1
                time.sleep(self.delay)
                
        new_Temperature = float("{0:0.1f}".format(float("{0:0.1f}".format(numpy.mean(avg_temp_Data))) ))
        new_Humidity = float("{0:.2f}".format(numpy.mean(avg_humidity_Data)))
        
        sql_update('temp', new_Temperature, self.zone, 'Update Temp Initial')
        sql_update('humidity', new_Humidity, self.zone, 'Update Humidity Initial')

        os.system('clear')
        log("Done Getting Temp")
        time.sleep(1)
        ### Start Forever loop to keep temp and humidity updated.
        try:
            startup = 0
            while (end_Thread == 0):
                humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
                if humidity is not None and temperature is not None:
                    temperature = (temperature*(9/5)+32) # Convert to F 
                    avg_temp_Data.append(temperature) # Add new data to average array
                    avg_humidity_Data.append(humidity) # Add new data to average array
                    del avg_temp_Data[0] # Remove oldest entry in average
                    del avg_humidity_Data[0] # Remove oldest entry in average
                    
                    ## Format Data
                    new_Temperature = float("{0:0.1f}".format(float("{0:0.1f}".format(numpy.mean(avg_temp_Data))) ))
                    new_Humidity = float("{0:.2f}".format(numpy.mean(avg_humidity_Data)))
                    ## Update data to DB
                    sql_update('temp', new_Temperature, self.zone, 'Update Temp')
                    sql_update('humidity', new_Humidity, self.zone, 'Update Humidity')
                    
                    # Update MQTT
                    self.mq.publish("/tstat/upstairs/temp", new_Temperature)
                time.sleep(self.delay) # Sleep delay between readings, usually 1sec
            
        except (KeyboardInterrupt, SystemExit):
            end_Thread = 1
        
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
        sql_update('relay', '0', zone, "Initial Setup - Clear Relay in DB")
        motion = 1
        while (end_Thread == 0):
            now = datetime.now()
            string_Time = now.strftime('%b-%d-%I:%M:%S')
            time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
            
            try:
                temp = float(sql_fetch('temp', self.zone))
                backup_Temp = float(sql_fetch('backuptemp', self.zone))
                hold_Temp = float(sql_fetch('holdtemp', self.zone))
                hold = int(sql_fetch('hold', self.zone))
                set_Temp = float(sql_fetch('settemp', self.zone))
                relay = int(sql_fetch('relay', self.zone))
            except:
                log("Error pulling data - DB Modify")
            
            if (hold == 1): ## If hold is ON
                
                if (temp_Held == 0): ## If hold was not on previous
                    temp_Held = 1 ## Set value so hold only triggers once
                    run_Temp = hold_Temp ## Set temp
                    log("Temp Held - Temp set to: " + str(run_Temp))
                    send_Notification("Kitchen Room", ("Kitchen - Hold - Temp set to: " + str(run_Temp)))
                if (temp_Held == 1): ## If hold temp changes while on hold - maybe from gui
                    run_Temp = hold_Temp
                    
            if (hold == 0): ## If not holding
                
                if (temp_Held == 1): ## If temp was held
                    temp_Held = 0
                    run_Temp = set_Temp
                    log(("Hold Removed - Returning Temp to " + str(run_Temp) + " Current Temp: " + str(temp)))
                    send_Notification("Kitchen Zone", ("Kitchen - Hold Removed - Temp set to: " + str(run_Temp)+ " Current Temp: " + str(temp)))
                if (motion == 1):   ## Not Holding and IS Motion      
                    run_Temp = set_Temp
                    
            try:
                if (startup == 0): ## Only do Logic after initial temp average
                    ## Gives a .5 degree flux to avoid triggering heat on and off repeaditly if temp is close
                    ## Also only triggers if relay is off already to avoid constantly triggering
                    if (((float(temp) + .5) < float(run_Temp)) and (relay == 0)): 
                        try:
                            
                            relay_On(self.zone)
                            log("Turned on Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Starting Relay")
                    elif ((float(temp) > float(run_Temp)) and (relay == 1)):
                        try:
                            relay_Off(self.zone)
                            log("Turned off Heat - Temp: " + str(temp))
                        except:
                            log("Error in : DB Modify - Stopping Relay")
            except:
                log("Error in : DB Modify - Execution")
            
            time.sleep(.1)
####################
## Functions
####################

def relay_On(zone):
    relay_State = int(sql_fetch('relay', zone))
    conn = MySQLdb.connect("192.168.68.112","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    try:
        relay_State = 1
        sql_update('relay', relay_State, zone, 'relay_On')
    except:
        log('Error turning ON relay')
    
    

def relay_Off(zone):
    relay_State = int(sql_fetch('relay', zone))
    conn = MySQLdb.connect("192.168.68.112","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    
    try:
        relay_State = 0
        sql_update('relay', relay_State, zone, 'relay_Off')
    except:
        log("Database Error in Relay Off")

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

def sql_update(field, value, zone, msg):
    ## Connect to SQL DB
    try:
        conn = MySQLdb.connect("192.168.68.112","pi","python","thermostat", port=3306 )
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
        conn = MySQLdb.connect("192.168.68.112","pi","python","thermostat", port=3306 )
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


##########################
## Main Loop
##########################

try:
    while (end_Thread == 0):
        ##Update Activity Monitor
        now = time.time()
        sql_update("last_updated", now, zone, "Update Activity")


except (KeyboardInterrupt, SystemExit):
    end_Thread = 1
    send_Notification("Kitchen Zone", "Kitchen - Thermostat App Closing")
   

    DB.join()
    motion.join()
    Data.join()

    sys.exit()
