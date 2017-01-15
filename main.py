import RPi.GPIO as GPIO
from time import *
import _thread
from datetime import datetime
import sys
from dht11 import *

#Globals
global relaypin
global pirpin
global new_Temperature
global new_Humidity
global relay_State
global set_Temp
global backup_Temp


## Setup Vars

pin1 = 4 #Red LED
buttonpins = [20, 21] # Switch 1,2 used for Temp Up and Down
button2 = 20 #button for increase temp
button1 = 21 # Button for decreses temp
relaypin = 23 # Pin connected to relay
pirpin = 5 # Pin connected to PIR
relay_State = 0 # State of relay, so relay is not constantly being triggered on or off
set_Temp = 60 # Temperature setpoint
backup_Temp = 58 # used for no motion
time_prev = int(time.time()) #used in delays
main_print_delay = 60 # Used in main loop for time delay for print debug statement
stop_button = 16

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
#Functions
#################

def button_push( threadname, pin, action): ## Should work to have more consistant button pushes
    GPIO.setmode(GPIO.BCM)
    #GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)#
   
    global set_Temp
    while True:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP) ##
        #input_state = GPIO.input(pin)
        if (GPIO.input(pin) == GPIO.LOW): ## Button to Increase The Set Temp Value
            
            if (action == "up"):
                set_Temp += 1
            elif (action == "down"):
                set_Temp -= 1
            elif (action == "exit"):
                sys.exit()
                print("exit")
                
            print("The Set Temp is Now", set_Temp)
        sleep(.2)

def exit_button( threadname, pin):
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    input_state = GPIO.input(pin)
    try:
        while True:
            if (GPIO.input(pin) == GPIO.LOW):
                sys.exit()
                print("exit")
    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()
            
def th_Update( threadname, delay): #keep temp and humidity updated in background
    #Global Vars
    global new_Temperature
    global new_Humidity
    new_Temperature = pull_Temperature()
    old_Temperature = 0
    new_Humidity = pull_Humidity()
    old_Humidity = 0
    try:
        while True:

            current_Temp = pull_Temperature() #pull current temp

            if ((current_Temp != False)): # if it has a value and not over 5 degrees les
                new_Temperature = current_Temp

            if (new_Temperature != old_Temperature): ## Temp Changed
#                print("Temperature changed to: " + str(new_Temperature) + "F")
                old_Temperature = new_Temperature

            ## Get current Humidity

            current_Humidity = pull_Humidity()
            if (current_Humidity != False):
                new_Humidity = current_Humidity
            if (new_Humidity != old_Humidity):
#                print("Humidity changed to: " + str(new_Humidity) + " %")
                old_Humidity = new_Humidity
            sleep(5)

    except (KeyboardInterrupt, SystemExit):
        GPIO.cleanup()

def motion_detect( threadname, pin, delay):
    global set_Temp
    global backup_Temp

    time_prev = int(time.time())
    prev_set_Temp = set_Temp
    no_motion_delay = 600
    temp_overriden = 0
    GPIO.setup(pirpin, GPIO.IN)
    while True:
        i = GPIO.input(pin)
        time_now = time.time()
        #print (i)
        if (i == 0):
            time_prev = int(time.time())
            while (i == 0):
                i = GPIO.input(pin)
                time_now = int(time.time())
                if ((time_now >= (time_prev + no_motion_delay)) and (temp_overriden == 0)):
                    prev_set_Temp = set_Temp
                    set_Temp = backup_Temp
                    temp_overriden = 1
                    print("No Motion, Temp Set to: " + str(backup_Temp))
                    
        elif (i == 1):
            if (temp_overriden == 1):
                set_Temp = prev_set_Temp
                print("Motion Detected, Returning Temp to: " + str(prev_set_Temp))
                temp_overriden = 0
            motion_detect = 1
            #print("Detected Motion")
            
            sleep(2)
        #print (i)
        sleep(.1)
        
def relay_On(pin):
    global relay_State
    global relaypin
    if (relay_State == 0):
        print("Relay ON")
        GPIO.setup(relaypin, GPIO.OUT) ## Relay SETUP
        GPIO.output(relaypin, GPIO.HIGH)
        #GPIO.output(ledpin, GPIO.HIGH)
        relay_State = 1
        print("Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
    elif (relay_State == 1):
        print("Relay Already ON")
        
def relay_Off(pin):
    global relay_State
    global relaypin
    if (relay_State == 1):
        print("Relay OFF")
        GPIO.setup(relaypin, GPIO.OUT) ## Relay SETUP
        GPIO.output(pin, GPIO.LOW)
        relay_State = 0
        print("Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
    elif (relay_State == 0):
        print("Relay Already OFF")

def user_Input( threadname, temp):
    global set_Temp
    
    while True:
        action = input("What do you want to do: ")

        if (action == "temp"):
            temp_change = input("What Temperature do you want to change to: ")
            set_Temp = int(temp_change)
            print("Temp Changed to: " + str(set_Temp))
        if (action == "help"):
            print("Current Commands are: temp, help, info")
        if (action == "info"):
            print("Main Loop Running, Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + "% Thermostat is set at: " + str(set_Temp) + "F Time is: " + strftime("%I:%M:%S"))
        action = 0


###############
#Call Button Threads
###############

try: ## Start threads for buttons
   _thread.start_new_thread( button_push, ("Temp Increase", button1, "up" ) )
   _thread.start_new_thread( button_push, ("Temp Decrease", button2, "down" ) )
   _thread.start_new_thread( button_push, ("Exit Buton", stop_button, "exit"))
except:
   print ("Error: Button Thraeds")


###############################
## Here to start thread for temp/humidity monitoring
###############################
try:
    _thread.start_new_thread( th_Update, ("TH Update", 10))
except:
    print ("Error Starting Temp Update")

#################################
##Start Motion Detection
#################################
try:
    _thread.start_new_thread( motion_detect, ("Detect Motion", pirpin, 30))
except:
    print("Error Starting Motion Detection")

try:
    _thread.start_new_thread( user_Input, ("User Input", set_Temp))
except:
    print("Error Starting User Input")
    
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
        
        time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
                
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
    GPIO.cleanup()
