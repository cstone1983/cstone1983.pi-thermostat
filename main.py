import RPi.GPIO as GPIO
import time
import threading
from datetime import datetime
import sys
import dht
import numpy
import os
import lcddriver
import http.client, urllib

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

pin1 = 4 #Red LED
buttonpins = [20, 21] # Switch 1,2 used for Temp Up and Down
button2 = 20 #button for increase temp
button1 = 21 # Button for decreses temp
relaypin = 23 # Pin connected to relay
pirpin = 5 # Pin connected to PIR
relay_State = 0 # State of relay, so relay is not constantly being triggered on or off
set_Temp = 63.5 # Temperature setpoint
backup_Temp = 58 # used for no motion
time_prev = int(time.time()) #used in delays
main_print_delay = 60 # Used in main loop for time delay for print debug statement
stop_button = 16
avg_Time = 30 #Number of Temp Reads in array average
avg_Delay = .4
hold_Temp = 0
end_Thread = 0


## Setup GPIO
GPIO.setmode(GPIO.BCM) # Board Setup

GPIO.setup(pin1, GPIO.OUT) #LED Setup

GPIO.setup(relaypin, GPIO.OUT) ## Relay SETUP

GPIO.setup(pirpin, GPIO.IN) # PIR Setup

GPIO.output(relaypin, GPIO.LOW) ## Relay SETUP

GPIO.setwarnings(False)

for i in buttonpins: # Setup buttons
    GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)

#################
#Thread Classes
#################

    
class ButtonPush(threading.Thread):
    def __init__(self, pin, action):
        threading.Thread.__init__(self)
        self.pin = pin
        self.action = action
    def run(self):
        #GPIO.setmode(GPIO.BCM)
        #GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)#
       
        global set_Temp
        global end_Thread
        global backup_Temp
        global hold_Temp
        while (end_Thread == 0):
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) ##
            input_state = GPIO.input(self.pin)
            if (input_state == 0): ## Button to Increase The Set Temp Value
                
                if (self.action == "up"):
                    set_Temp += 1
                elif (self.action == "down"):
                    set_Temp -= 1
                elif (self.action == "hold"):
                    if (hold_Temp == 0):
                        previous_Temp = int(set_Temp)
                        hold_Temp = 1
                        set_Temp = backup_Temp
                    elif (hold_Temp == 1):
                        hold_Temp = 0
                        set_Temp = int(previous_Temp)
                        
                        
                print("The Set Temp is Now", set_Temp)
                time.sleep(.3)
            else:
                time.sleep(.1)
        GPIO.cleanup()
  
class Update_Data(threading.Thread):
    def __init__(self, delay, avg_Time):
        threading.Thread.__init__(self)
        self.delay = delay
        self.avg_Time = avg_Time

    def run(self):
        global new_Temperature
        global new_Humidity
        global display
        global end_Thread
        global avg_temp_Data
        global avg_humidity_Data
        new_Temperature = "Calc." #sets initial temp to 100 so relay wont kick on while doing the average
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
        try:
            while (end_Thread == 0):
                result = instance.read()
                if result.is_valid():
                    current_Temp = result.temperature #pull current temp
                    current_Temp = (current_Temp*(9/5)+32)
                    if (int(current_Temp > 32)):
                        avg_temp_Data.append(current_Temp)
                        del avg_temp_Data[0]
                        new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data)))
                        #print (new_Temperature)
                    
                        
                ## Get current Humidity

                current_Humidity = result.humidity
                if (current_Humidity != False):
                    avg_humidity_Data.append(current_Humidity)
                    del avg_humidity_Data[0]
                    new_Humidity = float("{0:2f}".format(numpy.mean(avg_humidity_Data)))
            
                time.sleep(self.delay) # Sleep delay between readings, usually 1sec

        except (KeyboardInterrupt, SystemExit):
            GPIO.setmode(GPIO.BCM)
            GPIO.cleanup()
        GPIO.cleanup()
        menu.join()
        
class Detect_Motion(threading.Thread):
    def __init__(self, pin, delay):
        threading.Thread.__init__(self)
        self.pin = pin
        self.delay = delay
    def run(self):
        global set_Temp
        global backup_Temp
        global time_left
        global hold_Temp
        global end_Thread
        global string_Time
        time_left = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(self.pin, GPIO.IN)
        time_prev = int(time.time())
        prev_set_Temp = set_Temp
        no_motion_delay = 900 # 15 Min
        temp_overriden = 0 #used so set_temp only gets changed once
        
        try:
            while (end_Thread == 0):
                GPIO.setmode(GPIO.BCM)
                i = GPIO.input(self.pin)
                time_now = time.time()
                print (str(i) + " " + str(hold_Temp))
                if (i == 0):
                    time_prev = int(time.time())
                    while ((i == 0) and (hold_Temp == 0)):
                        i = GPIO.input(self.pin)
                        time_now = int(time.time())
                        print(time_left)
                        time_left = ((time_prev + no_motion_delay) - time_now)
                        if ((time_now >= (time_prev + no_motion_delay)) and (temp_overriden == 0)):
                            prev_set_Temp = set_Temp
                            set_Temp = backup_Temp
                            temp_overriden = 1
                            print("\n" + string_Time + " No Motion, Temp Set to: " + str(backup_Temp))
                            send_Notification("Living Room", ("No Motion, Temp set to: " + str(backup_Temp)))
                        time.sleep(1) 
                elif ((i == 1) and (hold_Temp == 0)):
                    if (temp_overriden == 1):
                        set_Temp = prev_set_Temp
                        print("\n" + string_Time + " Motion Detected, Returning Temp to: " + str(prev_set_Temp))
                        send_Notification("Living Room", ("Motion Detected, Temp Returned to: " + str(prev_set_Temp)))
                        temp_overriden = 0
                    motion_detect = 1
                    #print("Detected Motion")
                    
                    time.sleep(1)
                print (str(i) + " " + str(hold_Temp))
                time.sleep(.1)
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
        screen_print()
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
                backup_Temp = int(backup_Temp)
                backup_Temp = int(do_this)
            elif (action == "motion"):
                time_left_min = int(time_left / 60)
                time_left_sec = time_left - (time_left_min * 60)
                print("Time left untill motion timeout is: " + str(time_left_min) + " Minutes and " + str(time_left_sec) + " seconds")
            elif (action == "hold"):
                do_this = input("Do you want to hold the temp?(yes/no)")
                if (do_this == "yes"):
                    hold_Temp = 1
                    hold_Temp_at = input("What do you want to hold the time at? ")
                    previous_Temp = float(set_Temp)
                    set_Temp = float(hold_Temp_at)
                    print("\nTemp Set to " + str(set_Temp) + " and will be held here untill set otherwise.")
                elif (do_this == "no"):
                    hold_Temp = 0
                    set_Temp = float(previous_Temp)
                    print("\nTemp Returning to previously set - " + str(set_Temp))
            elif (action == "notify"):
                send_Notification("test", screen_print())
                
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
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    try:
        GPIO.output(pin, GPIO.HIGH)
        relay_State = 1
    except:
        print("Error Starting Relay")
        relay_State = 0


def relay_Off(pin):
    global relay_State
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    try:
        GPIO.output(pin, GPIO.LOW)
        relay_State = 0
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
def log_Info(message):
    global relay_State
    global string_Time
    global new_Temperature
    global new_Humidity

    
    
    
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

try:
    up_button = ButtonPush(button1, "up")
    down_button = ButtonPush(button2, "down")
    hold_button = ButtonPush(stop_button, "hold")
    down_button.start()
    hold_button.start()
    up_button.start()
    
except:
    print("Error Starting Buttons")

###############################
## Here to start thread for temp/humidity monitoring
###############################
try:
    Data = Update_Data(avg_Delay, avg_Time)
    Data.start()
#    Data.join()
except:
    print ("Error Starting Temp Update")

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
            if (hold_Temp == 0):
                show2 = str("Set: " + str(set_Temp) + " " + str(heat_State))
                show1 = str("T: " + str(new_Temperature) + " H: " + str(new_Humidity))
                display.lcd_display_string(show1, 1)
                display.lcd_display_string(show2, 2)
            elif (hold_Temp == 1):
                show2 = str("Temp Hold: " + str(set_Temp) + "         ")
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
                    send_Notification("Living Room", ("Heater is -ON- and the Temp is: " + str(new_Temperature)))
                    
                except:
                    print("\nError Starting Relay")
            elif ((float(new_Temperature) > float(set_Temp)) and (relay_State == 1)):
                try:
                    relay_Off(relaypin)
                    send_Notification("Living Room", ("Heater is -OFF- and Temp is: " + str(new_Temperature)))
                    print(screen_print())
                except:
                    print("\nError Stopping Relay")
                    
        time.sleep(.1)        

        


except (KeyboardInterrupt, SystemExit):
    send_Notification("Living Room", "Thermostat App Closing")
    GPIO.setmode(GPIO.BCM)
    GPIO.cleanup()
print("Exiting...")
GPIO.cleanup()
up_button.join()
down_button.join()
hold_button.join()
motion.join()
Data.join()

sys.exit()
