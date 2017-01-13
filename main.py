import RPi.GPIO as GPIO
from time import *
import _thread
from datetime import datetime
import sys
from dht11 import *
## Setup Vars

pin1 = 4 #Red LED
buttonpins = [20, 21] # Switch 1,2 used for Temp Up and Down
button2 = 20
button1 = 21
pin4 = 16
relaypin = 23


## Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin1, GPIO.OUT)
GPIO.setwarnings(False)
GPIO.setup(relaypin, GPIO.OUT) ## Relay SETUP
GPIO.output(relaypin, GPIO.LOW) ## Relay SETUP

for i in buttonpins:
    GPIO.setup(i, GPIO.IN, pull_up_down=GPIO.PUD_UP)

## Global Vars
global new_Temperature
global new_Humidity
global relay_State
global set_Temp
relay_State = 0
set_Temp = 60

#################
#Functions
#################

def button_push( threadname, pin, move): ## Should work to have more consistant button pushes
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    input_state = GPIO.input(pin)
    global set_Temp
    while True:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        if (GPIO.input(pin) == GPIO.LOW): ## Button to Increase The Set Temp Value
            
            if (move == "up"):
                set_Temp += 1
            elif (move == "down"):
                set_Temp -= 1

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

            if (current_Temp != False): # if it has a value
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

        
def relay_On(pin):
    global relay_State
    if (relay_State == 0):
        print("Relay ON")
        GPIO.output(relaypin, GPIO.HIGH)
        #GPIO.output(ledpin, GPIO.HIGH)
        relay_State = 1
        print("Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
    elif (relay_state == 0):
        print("Relay Already ON")
        
def relay_Off(pin):
    global relay_State
    if (relay_State == 1):
        print("Relay OFF")
        GPIO.output(pin, GPIO.LOW)
        #GPIO.output(ledpin, GPIO.LOW)
        relay_State = 0
        print("Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
    elif (relay_State == 0):
        print("Relay Already OFF")
###############
#Call Button Threads
###############

try: ## Start threads for buttons
   _thread.start_new_thread( button_push, ("Temp Increase", button1, "up" ) )
   _thread.start_new_thread( button_push, ("Temp Decrease", button2, "down" ) )
   _thread.start_new_thread( exit_button, ("Exit Buton", 16))
except:
   print ("Error: Button Thraeds")


###############################
## Here to start thread for temp/humidity monitoring
###############################
try:
    _thread.start_new_thread( th_Update, ("TH Update", 10))
except:
    print ("Error Starting Temp Update")


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
        sleep(2)
        time_now = int(time.time()) ## Keep current time updated for use in counter and motion sensor
        #print("Main Loop Running, Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
        sleep(10)
        if ((new_Temperature > set_Temp) and (relay_State == 1)):
            relay_Off(relaypin)
        elif (( (new_Temperature + .5) < set_Temp) and (relay_State == 0)):
            relay_On(relaypin)
                


        


except (KeyboardInterrupt, SystemExit):
    GPIO.cleanup()
