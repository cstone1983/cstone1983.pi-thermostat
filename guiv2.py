from tkinter import *
#import pymysql.cursors
import MySQLdb
import time
from datetime import datetime

global DB_Temp  #Temp var from update_from_DB used to display current temp
global DB_set_Temp #Current Set Temp from update_from_DB
global away_hold
global debug
global zone

away_hold = 60
GUI = 1
set_Temp = 0 #set var before updated from DB
DB_Temp = 0 #set var before updated from DB
DB_set_Temp = 0 #set var before updated from DB
debug = 0
zone = 'living'

## Setup Main Window

root = Tk()
root.title('Raspberry Pi Thermostat')
root.geometry('{}x{}'.format(800, 480)) #Format for 7" Touchscreen
root.attributes("-fullscreen", True)


## GUI Functions ##

def temp_up():
    new_Temp = 60
    global DB_set_Temp
    global zone
    new_Temp = DB_set_Temp + 1
    print("Temp UP to ", (new_Temp))
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    sql = ("UPDATE settings set settemp = %s WHERE zone = %s""")
    val = (new_Temp, zone)
    c.execute(sql, val)
    conn.commit()

def temp_down():
    new_Temp = 60
    global DB_set_Temp
    new_Temp = DB_set_Temp - 1
    print("Temp UP to ", (new_Temp))
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    sql = ("UPDATE settings set settemp = %s WHERE zone = %s""")
    val = (new_Temp, zone)
    c.execute(sql, val)
    conn.commit()

def debug_msg(message):
    global debug
    
    if message == "Toggle":
        print("Inside Toggle")
        if debug == 1:
            debug = 0
            print("Debug OFF")
            debug_button_msg.set("Debug OFF")
            
            #debug_button_msg.set("")
            
        else:
            debug = 1
            print("Debug ON")
            debug_button_msg.set("Debug ON")
            
    
            
        #debug_label_msg.set("")
    else:
        if debug == 1:
            now = datetime.now()
            string_Time = now.strftime('%b-%d-%I:%M:%S')
            debug_button_msg.set(string_Time + " - " + str(message))
            
def away(): #Hold temp while out of house. eleminate dog setting motion off
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    global away_hold
    global zone    
    global hold
    if (hold == 0):
        try:
            hold = 1
            sql = ("UPDATE settings SET hold = %s WHERE zone = %s")
            val = (hold, zone)
            c.execute(sql, val)
            conn.commit()
        except:
            debug_msg("Error Updating DB")

def sleep():
    ## Ideas
    # When have multiple zones setup use this to turn bedroom on and shutdown living room for night
    # For now shutdown living room untill specified time aka hold until.
    
    debug_msg("Coming Soon")

def end(): ## EXIT GUI
    root.destroy()

def keypad(field):

    global pin
    global hold
    global keyp
    # Setup DB Connection
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    
    def code(value): #Run after each keypress
        global keyp
        global pin
        
        if value == '<--':# remove last number
            pin = pin[:-1]
            e.delete('0', 'end')
            e.insert('end', pin)

        elif value == 'Set':
            # check Temp
            print("Checking Temp")
            if (int(pin) > 49 and int(pin) < 76):
                print("Temp OK")
                try:
                    sql = """UPDATE settings SET holdtemp = %s WHERE zone = %s"""
                    val = (pin, zone)
                    c.execute(sql, val)
                    conn.commit()
                    hold = 1
                    sql = """UPDATE settings SET hold = %s WHERE zone = %s"""
                    val = (hold, zone)
                    c.execute(sql, val)
                    conn.commit()
                    print("Hold Set")
                except:
                    debug_msg("error updating hold to DB")
                keyp.quit()
                keyp.destroy()
            else:
                debug_msg("Temp Error outside range")
                keyp.destroy()
                pin = ''
                # clear
                e.delete('0', 'end')
        else:
            # add number
            pin += value
            # add number to `entry`
            e.insert('end', value)

    if(hold == 0): #if Hold is not on then display keypad to set temp

        keys = [ #Keys in keypad
            ['1', '2', '3'],    
            ['4', '5', '6'],    
            ['7', '8', '9'],    
            ['<--', '0', 'Set'],    
        ]

        # create global variable for pin
        pin = '' # empty string

        keyp = Tk()
        keyp.title('Enter ' + field + ' Value')
        keyp.geometry('{}x{}'.format(800, 480))
        keyp.configure(bg="black")
        # place to display pin
        e = Entry(keyp)
        e.grid(row=0, column=0, columnspan=3, ipady=5)

        # create buttons using `keys`
        for y, row in enumerate(keys, 1):
            for x, key in enumerate(row):
                # `lambda` inside `for` has to use `val=key:code(val)` 
                # instead of direct `code(key)`
                b = Button(keyp, text=key, width=3, height=3, font=("Helvetica", 14), bg="black", fg="white", activebackground="black", activeforeground="white", command=lambda val=key:code(val))
                b.grid(row=y, column=x, ipadx=10, ipady=10)

        keyp.mainloop()
    else: # If hold is already set...Clear Hold
        hold = 0
        sql = ("""UPDATE settings SET hold = %s WHERE zone = %s""")
        val = (hold, zone)
        c.execute(sql, val)
        conn.commit()
        
def update_from_DB():
    ## Keep Data Current from DB
    global DB_set_Temp
    global backup_Temp
    global end_Thread
    global hold_Temp
    global temp_overriden
    global last_motion
    global hold
    global DB_Temp
    global DB_relay
    global DB_humidity
    
    try:
        conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)
        c.execute("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion, temp , relay , humidity FROM settings WHERE zone = 'living'")
        row = c.fetchone()
        # Store Data from DB
        DB_set_Temp = float(row['settemp'])
        #print(DB_set_Temp)
        backup_Temp = float(row['backuptemp'])
        hold_Temp = int(row['holdtemp'])
        #print(hold_Temp)
        last_motion = int(row['lastmotion'])
        motion = int(row['motion'])
        hold = int(row['hold'])
        #print(hold)
        DB_Temp = float(row['temp'])
        DB_relay = float(row['relay'])
        DB_humidity = float(row['humidity'])
        #print(hold)
        
    except:
        debug_msg("DB Error in update_from_DB")
        
        time.sleep(1)
    
    current_temp.set (str("Current Temp is: ")+str(DB_Temp)+" "+chr(176)+" F - "+str("Set Temp is: ")+str(DB_set_Temp)+chr(176)+" F ")
    title_var.set ("Raspberry Pi Home Thermostat - Zone - "+"Living")    ## Change to var when SQL above uses var for zone
    DB_humidity = str(DB_humidity)
    humidity_status.set (str(DB_humidity) + " %")    
    if (hold == 1):
        hold_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
        hold_button_txt.set(str("Held @ ")+str(hold_Temp))
    else:
        hold_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
        hold_button_txt.set(str("Hold"))
    if DB_relay == 1:
        relay_status2.set (str("ON"))
        relay_status_label.configure(fg="green")
    elif DB_relay == 0:
        relay_status2.set (str("OFF"))
        relay_status_label.configure(fg="red")
    root.after(400, update_from_DB)


# create all of the main containers
top_frame = Frame(root, bg='black', width=800, height=100, pady=3)
center = Frame(root, bg='gray2', width=800, height=200, padx=3, pady=3)
btm_frame = Frame(root, bg='black', width=800, height=110, pady=3)
btm_frame2 = Frame(root, bg='lavender', width=800, height=50, pady=3)

# layout all of the main containers
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

top_frame.grid(row=0, sticky="ew")
top_frame.grid_columnconfigure(1, weight=1)
center.grid(row=1, sticky="nsew")
btm_frame.grid(row=3, sticky="ew")
btm_frame.grid_rowconfigure(0, weight=1)
btm_frame.grid_columnconfigure(5, weight=1)
#btm_frame2.grid(row=4, sticky="ew")


# create the center widgets
center.grid_rowconfigure(0, weight=1)
center.grid_columnconfigure(1, weight=1)

ctr_left = Frame(center, bg='black', width=200, height=200)
ctr_mid = Frame(center, bg='black', width=400, height=200, padx=3, pady=3)
ctr_mid.grid_columnconfigure(0, weight=1)
ctr_mid.grid_rowconfigure(0, weight=1)
ctr_right = Frame(center, bg='black', width=200, height=200, padx=3, pady=3)
ctr_left.grid_columnconfigure(0, weight=1)
ctr_left.grid(row=0, column=0, sticky="ns")
ctr_mid.grid(row=0, column=1, sticky="nsew")
ctr_right.grid(row=0, column=2, sticky="ns")

#### Status Lables


## Zone Selection

zone = StringVar(top_frame)
zone="Living"
option = OptionMenu(top_frame, zone, "one", "two", "three", "four")
option.grid(row=1, column=0)

## Title
title_var = StringVar()

title_label = Label(top_frame, textvariable=title_var, font=("Helvetica", 16), bg = "black", fg="white")
title_label.grid(row=0, column=0, columnspan=4)
##Current Temp

current_temp = StringVar()
set_temp = StringVar()

temp_label = Label(top_frame, textvariable=current_temp, font=("Helvetica", 16), bg = "black", fg="white")
current_temp.set (str("Current Temp is: ")+str(DB_Temp)+" "+chr(176)+str("Set Temp is: ")+str(DB_set_Temp))
temp_label.grid(column=1, row=1)

## Temp Control Buttons

up = Button(ctr_left, text="Temp UP",command=temp_up, width=15,height=5, padx=3, bg="black", fg="white", activebackground="black", activeforeground="white")
down = Button(ctr_left, text="Temp Down", command=temp_down, width=15, height=5, padx=3, pady=3, bg="black", fg="white", activebackground="black", activeforeground="white")
down.pack(side=BOTTOM)
up.pack(side=BOTTOM)


## Exit Button

close = Button(top_frame, text="Exit", command=end, height=2, width=10, bg="black", fg="white", activebackground="black", activeforeground="white")

close.grid(row=1, column=3, sticky=E)

## Hold Button

hold_button_txt = StringVar()
hold_button_txt.set(str("Hold"))
hold_button = Button(ctr_mid, textvariable=hold_button_txt, width=15,height=5, padx=3, command=lambda: keypad("hold"), bg="black", fg="white", activebackground="black", activeforeground="white")
hold_button.grid(row=1, column=1)

## Away Button

away_button_txt = StringVar()
away_button_txt.set(str("Away"))
away_button = Button(ctr_mid, textvariable=away_button_txt, width=15,height=5, padx=3, command=away, bg="black", fg="white", activebackground="black", activeforeground="white")
away_button.grid(row=2, column=1)

## Sleep Button

sleep_button_txt = StringVar()
sleep_button_txt.set(str("Sleep"))
sleep_button = Button(ctr_mid, textvariable=sleep_button_txt, width=15,height=5, padx=3, command=sleep, bg="black", fg="white", activebackground="black", activeforeground="white")
sleep_button.grid(row=3, column=1)

## relay status


relay_status = StringVar()
relay_status2 = StringVar()
relay_label = Label(btm_frame, textvariable=relay_status, font=("Helvetica", 16), bg = "black", fg="white")
relay_status.set (str("Heat: "))
relay_label.grid(column=0, row=1)
relay_status_label = Label(btm_frame, textvariable=relay_status2, font=("Helvetica", 16), bg = "black", fg="white")
relay_status_label.grid(column=1,row=1)

## Humidity
humidity_status = StringVar()
humidity_label = Label(btm_frame, text=" Humidity: ",font=("Helvetica", 16), bg = "black", fg="white") 
humidity_status_label = Label(btm_frame, textvariable=humidity_status,font=("Helvetica", 16), bg = "black", fg="white") 
humidity_label.grid(column=3, row=1)
humidity_status_label.grid(column=4, row=1)

## Debug Status Label
debug_button_msg = StringVar()
debug_button = Button(btm_frame, textvariable=debug_button_msg, highlightthickness = 0, bd = 0, height=2, width=40, command=lambda: debug_msg("Toggle"), bg="black", fg="white", activebackground="black", activeforeground="white")
debug_button.grid(column=6, row=1)

## Run Main Window

root.after(1000, update_from_DB)
root.mainloop()









# create the widgets for the top frame
##model_label = Label(top_frame, text='Model Dimensions')
##width_label = Label(top_frame, text='Width:')
##length_label = Label(top_frame, text='Length:')
##entry_W = Entry(top_frame, background="pink")
##entry_L = Entry(top_frame, background="orange")
# layout the widgets in the top frame
##model_label.grid(row=0, columnspan=3)
##width_label.grid(row=1, column=0)
##length_label.grid(row=1, column=2)
##entry_W.grid(row=1, column=1)
##entry_L.grid(row=1, column=3)
