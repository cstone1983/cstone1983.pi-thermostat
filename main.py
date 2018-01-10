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
import sqlite3 as lite

#Globals
global relaypin
global pirpin
global new_Temperature
global new_Humidity
global relay_State
global set_Temp
global backup_Temp
global hold_Temp
global display
global string_Time
global string_Info
global end_Thread


## Setup Vars
#Pin Numbers, Temp Sensor set in dht.py, lcd pins set in lcddriver
relaypin = 23 # Pin connected to relay
pirpin = 20 # Pin connected to PIR


relay_State = 0 # State of relay, so relay is not constantly being triggered on or off


## To Remove, will pull from DB always
set_Temp = 64.5 # Temperature setpoint

## To Remove, will pull from DB always
backup_Temp = 58 # used for no motion
time_prev = int(time.time()) #used in delays
avg_Time = 30 #Number of Temp Reads in array average
avg_Delay = 1 # Delay between temp readings
hold_Temp = 0 #used to hold temp from user input
hold = 0
end_Thread = 0 # Helps to end active threads


## Setup GPIO
GPIO.setmode(GPIO.BCM) # Board Setup
GPIO.setup(relaypin, GPIO.OUT) ## Relay SETUP
GPIO.output(relaypin, GPIO.LOW) ## Relay SETUP
GPIO.setwarnings(False)


## SQLite Connection

conn = lite.connect('thermostat.db')
c = conn.cursor()

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
        global avg_temp_Data
        global avg_humidity_Data
        global relay_State

        #### SQlite connection
        conn = lite.connect('thermostat.db')
        c = conn.cursor()

        
        new_Temperature = "Calc." #sets initial temp to 100 so relay wont kick on while doing the average
        new_Humidity = 0
        prev_time = int(time.time())
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
                    print(str((self.avg_Time - i)) + " Temp: " + str(get_Temp) + " Humidity: " + str(get_Humidity)) # Debugging print, end will proball show just dots or just countdown
                    i += 1
                    time.sleep(self.delay)
                  
        new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data))) # Do initial Average
        new_Humidity = float("{0:.2f}".format(numpy.mean(avg_humidity_Data)))
        os.system('clear')
        

        ###########
        # Start User Input
        ####################
        try:
        
            menu = Menu_System()
            menu.start()
            
        except:
            print("Error Starting User Input")
        
        ### Start Forever loop to keep temp and humidity updated.
        while (end_Thread == 0):
            result = instance.read()
            if result.is_valid():
                current_Temp = result.temperature #pull current temp
                current_Temp = (current_Temp*(9/5)+32) # Convert Temp to F
                if (int(current_Temp > 32)):
                    avg_temp_Data.append(current_Temp)
                    del avg_temp_Data[0]
                    new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data)))
                    
                    try:
                        c.execute("UPDATE settings SET temp = ? WHERE zone = 'living'", (new_Temperature,))
                        conn.commit()
                    except:
                        print("Database Error in Temp Data Update")
                        conn = lite.connect('thermostat.db')
                        c = conn.cursor()
                    conn.commit()
                                            
            ## Get current Humidity

            current_Humidity = result.humidity
            if (current_Humidity != False):
                avg_humidity_Data.append(current_Humidity)
                del avg_humidity_Data[0]
                new_Humidity = float("{0:2f}".format(numpy.mean(avg_humidity_Data)))
                new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data)))
                try:
                    c.execute("UPDATE settings SET humidity = ? WHERE zone = 'living'", (new_Humidity,))
                    conn.commit()
                except:
                        print("Database Error in Humidity Data Update")
                        conn = lite.connect('thermostat.db')
                        c = conn.cursor()
            try:
                time_now = int(time.time())
                if (time_now > (prev_time + 10)): 
                    c.execute("INSERT INTO data (zone, time, temp, humidity, heat) VALUES (?, ?, ?, ?, ?)", ('living', time_now, new_Temperature, new_Humidity, relay_State))
                    conn.commit()
                    prev_time = time_now
            except:
                print("Error Updating Data Table")
            time.sleep(self.delay) # Sleep delay between readings, usually 1sec
        

        GPIO.cleanup()
        print("Ending Update Data")

class DB_Modify(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global set_Temp
        global backup_Temp
        global end_Thread
        global hold_Temp
        global temp_overriden
        global last_motion
        global hold
        motion_Held = 0
        previous_Temp = backup_Temp
        conn = lite.connect('thermostat.db')
        c = conn.cursor()
        user_held = 0
        while (end_Thread == 0):
            try:

                c.execute("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion FROM settings WHERE zone = 'living'")
                row = c.fetchone()

                
                backup_Temp = float(row[1])
                hold_Temp = int(row[3])
                last_motion = int(row[4])
                motion = int(row[5])
                hold = int(row[2])
               
             
                if ((motion == 1) and (motion_Held == 0) and (hold == 0) and (user_held == 0)):
                    set_Temp = float(row[0])
                if ((hold == 1) and (user_held == 0)): ## User Holds (priority over no motion hold)
                    previous_Temp = set_Temp
                    user_held = 1
                    set_Temp = hold_Temp
                    c.execute("UPDATE settings set settemp = ? WHERE zone = 'living'", (set_Temp,))
                    conn.commit()
                    send_Notification("Living Room", ("User Held Temp to: " + str(hold_Temp)))
                elif((hold == 0) and (user_held == 1)):
                    set_Temp = previous_Temp
                    user_held = 0
                    c.execute("UPDATE settings set settemp = ? WHERE zone = 'living'", (set_Temp,))
                    conn.commit()
                    send_Notification("Living Room", ("User Restored Temp to: " + str(set_Temp)))                    
                    
                elif((hold == 0) and (user_held == 0)): ## Hold for no motion
                        
                    if ((motion == 0) and (motion_Held == 0)):
                        motion_Held = 1
                        previous_Temp = set_Temp
                        set_Temp = backup_Temp
                        c.execute("UPDATE settings set settemp = ? WHERE zone = 'living'", (set_Temp,))
                        conn.commit()
                        send_Notification("Living Room", ("Motion Held to: " + str(set_Temp)))
                        
                        print("Temp Held")
                    if ((motion == 1) and (motion_Held == 1)):
                        motion_Held = 0
                        set_Temp = previous_Temp
                        c.execute("UPDATE settings set settemp = ? WHERE zone = 'living'", (set_Temp,))
                        conn.commit()
                        send_Notification("Living Room", ("Motion Restored Temp to: " + str(set_Temp)))
                    
                    
                
                time.sleep(.2)
            except:
                print("DB Error in DB_Modify")
                conn = lite.connect('thermostat.db')
                c = conn.cursor()
                time.sleep(1)
        GPIO.cleanup()
        print("Ending DB Modify")

class Detect_Motion(threading.Thread):
    def __init__(self, pin, delay):
        threading.Thread.__init__(self)
        self.pin = pin
        self.delay = delay
    def run(self):
        global time_left
        global hold_Temp
        global end_Thread
        global string_Time
        global last_motion
        #### SQlite connection
        conn = lite.connect('thermostat.db')
        c = conn.cursor()


        time_left = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        #GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pir=MotionSensor(self.pin)        
        time_prev = int(time.time())
        prev_set_Temp = set_Temp
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
                time_now = int(time.time())
                
                try:
                    c.execute("UPDATE settings SET lastmotion = ? WHERE zone = 'living'", (time_now,))
                    c.execute("UPDATE settings set motion = 1 WHERE zone = 'living'")
                    conn.commit()
                except:
                    print("Database Error in Motion Update")
                    conn = lite.connect('thermostat.db')
                    c = conn.cursor()
                
                motion_detect = 1
                
            ### NO Motion
            elif ((motion <= 5)):
                
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
                    if ((time_now >= (last_motion + no_motion_delay))):
                        
                        try:
                            c.execute("UPDATE settings SET motion = 0 WHERE zone = 'living'")
                            conn.commit()
                        except:
                            print("Database Error in Motion Update")
                            conn = lite.connect('thermostat.db')
                            c = conn.cursor()
                time.sleep(1)

            

           
                
            time.sleep(.2)
        GPIO.setmode(GPIO.BCM)
        GPIO.cleanup()
        print("Ending Motion")
        
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
        screen_print()
        conn = lite.connect('thermostat.db')
        c = conn.cursor()
        while (end_Thread == 0):
            print(screen_print())
            action = input("\nWhat do you want to do: ")

            if (action == "temp"):
                do_this = input("What Temperature do you want to change to: ")
                try:
                    if (float(do_this) > 50 and float(do_this) < 80):
                        set_Temp = float(do_this)
                        print("Temp Changed to: " + str(set_Temp))
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
                backup_Temp = float(do_this)
                try:
                    conn = lite.connect('thermostat.db')
                    c = conn.cursor()
                    c.execute("UPDATE settings SET backuptemp = ? WHERE zone = 'living'", (backup_Temp,))
                except:
                    print("DB Error in DB_Modify")
            elif (action == "motion"):
                time_left_min = int(time_left / 60)
                time_left_sec = time_left - (time_left_min * 60)
                print("Time left untill motion timeout is: " + str(time_left_min) + " Minutes and " + str(time_left_sec) + " seconds")
            elif (action == "hold"):
                do_this = input("Do you want to hold the temp?(yes/no)")
                if (do_this == "yes"):
                    hold_Temp_at = input("What do you want to hold the time at? ")
                    c.execute("UPDATE settings SET holdtemp = ? WHERE zone = 'living'", (hold_Temp_at,))
                    c.execute("UPDATE settings SET hold = 1 WHERE zone = 'living'")
                    conn.commit()
                    time.sleep(1)
                elif (do_this == "no"):
                    c.execute("UPDATE settings SET hold = 0 WHERE zone = 'living'")
                    conn.commit()
            elif (action == "notify"):
                send_Notification("test", screen_print())
                
            elif (action == "data"):
                print(avg_temp_Data)
                print("\n" + str(avg_humidity_Data))
            elif (action == "exit"):
                send_Notification("Living Room", "Thermostat App Closing")
                end_Thread = 1
        
            action = 0
        print("Ending Menu")        
####################
## Functions
####################

def relay_On(pin):
    global relay_State
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = lite.connect('thermostat.db')
    c = conn.cursor()
    try:
        GPIO.output(pin, GPIO.HIGH)
        relay_State = 1
        try:
            c.execute("UPDATE settings SET relay = ? WHERE zone = 'living'", (relay_State,))
            conn.commit()
        except:
            print("Database Error in Relay ON")
    except:
        print("Error Starting Relay")
        relay_State = 0
    


def relay_Off(pin):
    global relay_State
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = lite.connect('thermostat.db')
    c = conn.cursor()
    try:
        GPIO.output(pin, GPIO.LOW)
        relay_State = 0
        try:
            c.execute("UPDATE settings SET relay = ? WHERE zone = 'living'", (relay_State,))
            conn.commit()
        except:
            print("Database Error in Relay ON")
            
    except:
        print("Error Stopping Relay")
        relay_State = 1
        

def send_Notification(title, body):
   
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
            "token": "awmq2qh4qoijvztozwuvte5qdbikhm",
            "user": "u9yffbyi7ppxhcw79xwfwg5afhszk2",
            "message": body,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
      
    
def screen_print():
    global relay_State
    if (relay_State == 1):
            string_Info = str("\n" + string_Time + " - Relay ON  - " + "Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
            
    elif (relay_State == 0):

            string_Info = str("\n" + string_Time + " - Relay OFF - " + "Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
    return string_Info

    print(string_Info)

    
############################################
## Setup Display
############################################
display = lcddriver.lcd()
display.lcd_clear()
    
print("Current Set Temp is: ", set_Temp)





###############
#Call Button Threads
###############
##
##try:
##    up_button = ButtonPush(button1, "up")
##    down_button = ButtonPush(button2, "down")
##    hold_button = ButtonPush(stop_button, "hold")
##    down_button.start()
##    hold_button.start()
##    up_button.start()
##    
##except:
##    print("Error Starting Buttons")

###############################
## Here to start thread for temp/humidity monitoring
###############################
try:
    Data = Update_Data(avg_Delay, avg_Time)
    Data.start()
#    Data.join()
except:
    print ("Error Starting Temp Update")

try:
    DB = DB_Modify()
    DB.start()
except:
    print("Error Starting DB Update")

#################################
##Start Motion Detection
#################################
try:
    motion = Detect_Motion(pirpin, 900)
    motion.start()
#   motion.join()
except:
    print("Error Starting Motion Detection")


    

##########################
## Main Loop
##########################

try:
    while (end_Thread == 0):
        
        now = datetime.now()
        string_Time = now.strftime('%b-%d-%I:%M:%S')
        
        ## Update Display
        if (relay_State == 1):
            heat_State = "    ON"
        elif (relay_State == 0):
            heat_State = "   OFF"
        try:
            if (hold == 1):
                show2 = str("Held At:  " + str(hold_Temp) + " " + str(heat_State))
            elif (hold == 0):
                show2 = str("Set: " + str(set_Temp) + " " + str(heat_State))
            show1 = str("T: " + str(new_Temperature) + " H: " + str(new_Humidity))
            display.lcd_display_string(show1, 1)
            display.lcd_display_string(show2, 2)
            
        except:
            print("Display error")
            display = lcddriver.lcd()
            display.lcd_clear()

        time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
        
        if (new_Temperature != "Calc."):
            if (( (float(new_Temperature) + .5) < float(set_Temp)) and (relay_State == 0)):
                try:
                    relay_On(relaypin)
                    print(screen_print())
                    #send_Notification("Living Room", ("Heater is -ON- and the Temp is: " + str(new_Temperature)))
                    
                except:
                    print("\nError Starting Relay")
            elif ((float(new_Temperature) > float(set_Temp)) and (relay_State == 1)):
                try:
                    relay_Off(relaypin)
                    #send_Notification("Living Room", ("Heater is -OFF- and Temp is: " + str(new_Temperature)))
                    print(screen_print())
                except:
                    print("\nError Stopping Relay")
                    
        time.sleep(.1)        

    print("Ending Main Loop")
    print("Exiting...")
    
    motion.join()
    Data.join()
    menu.join()
    exit()

except (KeyboardInterrupt, SystemExit):
    send_Notification("Living Room", "Thermostat App Closing")
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
print("Exiting...")
GPIO.cleanup()

motion.join()
Data.join()
menu.join()
sys.exit()
