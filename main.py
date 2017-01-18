import RPi.GPIO as GPIO
from time import *
import _thread
import threading
from datetime import datetime
import sys
import dht
from pushbullet import Pushbullet
import numpy
import os
#Globals
global relaypin
global pirpin
global new_Temperature
global new_Humidity
global relay_State
global set_Temp
global backup_Temp
global hold_Temp



## Setup Vars

pin1 = 4 #Red LED
buttonpins = [20, 21] # Switch 1,2 used for Temp Up and Down
button2 = 20 #button for increase temp
button1 = 21 # Button for decreses temp
relaypin = 23 # Pin connected to relay
pirpin = 5 # Pin connected to PIR
relay_State = 0 # State of relay, so relay is not constantly being triggered on or off
set_Temp = 63 # Temperature setpoint
backup_Temp = 58 # used for no motion
time_prev = int(time()) #used in delays
main_print_delay = 60 # Used in main loop for time delay for print debug statement
stop_button = 16
avg_Time = 60 #Span of time for Temperature average
hold_Temp = 0


## Setup GPIO
GPIO.setmode(GPIO.BCM) # Board Setup

GPIO.setup(pin1, GPIO.OUT) #LED Setup

GPIO.setup(relaypin, GPIO.OUT) ## Relay SETUP

GPIO.output(relaypin, GPIO.LOW) ## Relay SETUP

GPIO.setup(pirpin, GPIO.IN) # PIR Setup

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
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)#
       
        global set_Temp
        while True:
            #GPIO.setmode(GPIO.BCM)
            #GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) ##
            #input_state = GPIO.input(pin)
            if (GPIO.input(self.pin) == GPIO.LOW): ## Button to Increase The Set Temp Value
                
                if (self.action == "up"):
                    set_Temp += 1
                elif (self.action == "down"):
                    set_Temp -= 1
                elif (self.action == "exit"):
                    sys.exit()
                    print("exit")
                    
                print("The Set Temp is Now", set_Temp)
            sleep(.2)

class Update_Data(threading.Thread):
    def __init__(self, delay, avg_Time):
        threading.Thread.__init__(self)
        self.delay = delay
        self.avg_Time = avg_Time

    def run(self):
        global new_Temperature
        global new_Humidity
        global avg_temp_Data
        new_Temperature = 100 #sets initial temp to 100 so relay wont kick on while doing the average
        new_Humidity = 0
        instance = dht.DHT11(pin=19)
        ## Loop to set initial data for temp Average. Time of loop is based on avg_Time
        i = 0
        avg_temp_Data = []
        print("\nGetting Average Temperature...Please Wait..")
        while (i < self.avg_Time):
            result = instance.read()
            if result.is_valid():
                get_Temp = result.temperature
                get_Temp = (get_Temp*(9/5)+32)
                if (int(get_Temp) > 32): #Eliminate values under 32, most common errors were 32 and 0
                    avg_temp_Data.append(get_Temp)
                    i += 1
                    print(str((self.avg_Time - i)) + " Temp: " + str(get_Temp)) # Debugging print, end will proball show just dots or just countdown
                    sleep(1)
        new_Temperature = float("{0:.2f}".format(numpy.mean(avg_temp_Data))) # Do initial Average
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
            while True:
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
                    new_Humidity = current_Humidity

                sleep(self.delay) # Sleep delay between readings, usually 1sec

        except (KeyboardInterrupt, SystemExit):
            GPIO.cleanup()
class Detect_Motion(threading.Thread):
    def __init__(self, pin, delay):
        threading.Thread.__init__(self)
        self.pin = pin
        self.delay = delay
    def run(self):
        global set_Temp
        global backup_Temp
        global time_left
        time_left = 0
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.pin, GPIO.IN)
        time_prev = int(time())
        prev_set_Temp = set_Temp
        no_motion_delay = 900 # 15 Min
        temp_overriden = 0
        
        try:
            while True:
                i = GPIO.input(self.pin)
                time_now = time()
                #print (i)
                if (i == 0):
                    time_prev = int(time())
                    while ((i == 0) and (hold_Temp == 0)):
                        i = GPIO.input(self.pin)
                        time_now = int(time())
                        time_left = ((time_prev + no_motion_delay) - time_now)
                        if ((time_now >= (time_prev + no_motion_delay)) and (temp_overriden == 0)):
                            prev_set_Temp = set_Temp
                            set_Temp = backup_Temp
                            temp_overriden = 1
                            print("No Motion, Temp Set to: " + str(backup_Temp))
                            send_Notification("Living Room", ("No Motion, Temp set to: " + str(backup_Temp)), "send")
                            
                elif ((i == 1) and (hold_Temp == 0)):
                    if (temp_overriden == 1):
                        set_Temp = prev_set_Temp
                        print("Motion Detected, Returning Temp to: " + str(prev_set_Temp))
                        send_Notification("Living Room", ("Motion Detected, Temp Returned to: " + str(prev_set_Temp)), "send")
                        temp_overriden = 0
                    motion_detect = 1
                    #print("Detected Motion")
                    
                    sleep(2)
                #print (i)
                sleep(.1)
        except(KeyboardInterrupt, SystemExit):
            GPIO.cleanup()        

class Menu_System(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global set_Temp
        global new_Temperature
        global relay_State
        global backup_Temp
        global avg_temp_Data
        global time_left
        print(strftime('%I:%M:%S') + " Current Temp is: " + str(new_Temperature) + "F and Temp is set to: " + str(set_Temp))
        while True:
            
            action = input("\nWhat do you want to do: ")

            if (action == "temp"):
                do_this = input("What Temperature do you want to change to: ")
                set_Temp = int(do_this)
                print("Temp Changed to: " + str(set_Temp))
            elif (action == "help"):
                print("\n------------------")
                print("temp - Change Set Temperature")
                print("data - Show Current Average Data Set")
                print("backup temp - Set Backup Temp for No Motion aka Night")
                print("motion - Time left before motion timeout")
                print("exit - exit thermostat")
            elif (action == "info"):
                print(strftime("%I:%M:%S") + " Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + "% Thermostat is set at: " + str(set_Temp) + "F Time is: ")
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
                    previous_Temp = int(set_Temp)
                    set_Temp = int(hold_Temp_at)
                    print("\nTemp Set to " + str(set_Temp) + " and will be help here untill set otherwise.")
                elif (do_this == "no"):
                    hold_Temp = 0
                    set_Temp = int(previous_Temp)
                    print("\nTemp Returning to previously set - " + str(set_Temp))
                    
            elif (action == "exit"):
                GPIO.cleanup()
                sys.exit()
            
            elif (action == 'data'):
                print("\n" + str(avg_temp_Data))
            action = 0

####################
## Functions
####################


def relay_On(pin):
    global relay_State
    
    if (relay_State == 0):
        print("Relay ON")
        GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
        GPIO.output(pin, GPIO.HIGH)
        #GPIO.output(ledpin, GPIO.HIGH)
        relay_State = 1
          
        send_Notification("Living Room", ("Heater is on and the Temp is: " + str(new_Temperature)), 'send')
        
        print("\nCurrent Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp) + strftime("%I:%M:%S"))
    elif (relay_State == 1):
        print("Relay Already ON")
        
def relay_Off(pin):
    global relay_State
    if (relay_State == 1):
        print("Relay OFF")
        GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
        GPIO.output(pin, GPIO.LOW)
        relay_State = 0
        send_Notification("none", "none", "clear")
        send_Notification("Living Room", ("Heater is off and Temp is: " + str(new_Temperature)), 'send')
        print("Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp) + strftime("%I:%M:%S"))
    elif (relay_State == 0):
        print("Relay Already OFF")


 
def send_Notification(title, body, action):
    pb = Pushbullet('o.YYc1GgqyrOCPj1peMzmYaoI0aJw7YLyI')
    data = {
        'type':'note',
        'title':title,
        'body':body
        }
    #resp = requests.post('https://api.pushbullet.com/api/pushes',data=data, auth=(API_KEY,''))
    if (action == 'send'):
        push = pb.push_note(title, body)
    if (action == 'clear'):
        push = pb.delete_pushes()
###############
#Call Button Threads
###############

try:
    up_button = ButtonPush(button1, "up")
    down_button = ButtonPush(button2, "down")
    end_button = ButtonPush(stop_button, "exit")
    down_button.start()
    end_button.start()
    up_button.start()
    
except:
    print("Error Starting Buttons")

###############################
## Here to start thread for temp/humidity monitoring
###############################
try:
    Data = Update_Data(1, avg_Time)
    Data.start()
except:
    print ("Error Starting Temp Update")

#################################
##Start Motion Detection
#################################
try:
    motion = Detect_Motion(pirpin, 900)
    motion.start()
except:
    print("Error Starting Motion Detection")


    
############################################
## Opening Print to show current Setting
############################################
## Eventually Will Show to LCD or whatever display
    
print("Current Set Temp is: ", set_Temp)

##########################
## Main Loop
##########################
try:
    while True:
        
        time_now = int(time()) ## Keep current time updated for use in counter and motion sensor
               
        if (time_now >= (time_prev + main_print_delay)):
            ## Debug Messages
            #print("Main Loop Running, Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + "% Thermostat is set at: " + str(set_Temp) + "F Time is: " + strftime("%I:%M:%S"))
            #################
            time_prev = time_now
        sleep(5)
        if ((new_Temperature > set_Temp) and (relay_State == 1)):

                relay_Off(relaypin)
        elif (( (new_Temperature + .5) < set_Temp) and (relay_State == 0) and (new_Temperature != False)):
  
            relay_On(relaypin)
                


        


except (KeyboardInterrupt, SystemExit):
    send_Notification("Living Room", "Thermostat App Closing", "send")
    GPIO.cleanup()
    
