from tkinter import *
import sqlite3 as lite
import time

global DB_Temp  #Temp var from update_from_DB used to display current temp
global DB_set_temp #Current Set Temp from update_from_DB
GUI = 1
set_Temp = 0 #set var before updated from DB
DB_Temp = 0 #set var before updated from DB
DB_set_temp = 0 #set var before updated from DB

## Setup Main Window
root = Tk()
root.title('Raspberry Pi Thermostat')
root.geometry('{}x{}'.format(800, 480)) #Format for 7" Touchscreen


## GUI Functions ##

def temp_up():
    new_Temp = 60
    global set_Temp
    new_Temp = set_Temp + 1
    print("Temp UP to ", (new_Temp))
    conn = lite.connect('thermostat.db')
    c = conn.cursor()
    c.execute("UPDATE settings set settemp = ? WHERE zone = 'living'", (new_Temp,))
    conn.commit()

def temp_down():
    new_Temp = 60
    global set_Temp
    new_Temp = set_Temp - 1
    print("Temp UP to ", (new_Temp))
    conn = lite.connect('thermostat.db')
    c = conn.cursor()
    c.execute("UPDATE settings set settemp = ? WHERE zone = 'living'", (new_Temp,))
    conn.commit()
def end():
    root.destroy()
def keypad(field):
# inform function to use external/global variable
    global pin
    global hold
    global keyp
    # Setup DB Connection
    conn = lite.connect('thermostat.db')
    c = conn.cursor()
    
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
            if (str(pin) > "49" and str(pin) < "76"):
                print("Temp OK")
                try:
                    c.execute("UPDATE settings SET holdtemp = ? WHERE zone = 'living'", (pin,))
                    c.execute("UPDATE settings SET hold = 1 WHERE zone = 'living'")
                    conn.commit()
                    print("Hold Set")
                except:
                    print("error updating hold")
                keyp.distroy()
            else:
                print("Temp Error", pin)
                pin = ''
                # clear
                e.delete('0', 'end')
        else:
            print("number added")
            # add number
            pin += value
            # add number to `entry`
            e.insert('end', value)

    if(hold == 0): #if Hold is not on then display keypad to set temp

        keys = [ #Keys in keypad
            ['1', '2', '3'],    
            ['4', '5', '6'],    
            ['7', '8', '9'],    
            ['<--', '9', 'Set'],    
        ]

        # create global variable for pin
        pin = '' # empty string

        keyp = Tk()

        # place to display pin
        e = Entry(keyp)
        e.grid(row=0, column=0, columnspan=3, ipady=5)

        # create buttons using `keys`
        for y, row in enumerate(keys, 1):
            for x, key in enumerate(row):
                # `lambda` inside `for` has to use `val=key:code(val)` 
                # instead of direct `code(key)`
                b = Button(keyp, text=key, command=lambda val=key:code(val))
                b.grid(row=y, column=x, ipadx=10, ipady=10)

        keyp.mainloop()
    else: # If hold is already set...Clear Hold
        c.execute("UPDATE settings SET hold = 0 WHERE zone = 'living'")
        conn.commit()
        
def update_from_DB():
    ## Keep Data Current from DB
    global set_Temp
    global backup_Temp
    global end_Thread
    global hold_Temp
    global temp_overriden
    global last_motion
    global hold
    global DB_Temp
    try:
        conn = lite.connect('thermostat.db')
        c = conn.cursor()
        c.execute("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion, temp FROM settings WHERE zone = 'living'")
        row = c.fetchone()
        # Store Data from DB
        set_Temp = float(row[0])
        backup_Temp = float(row[1])
        hold_Temp = int(row[3])
        last_motion = int(row[4])
        motion = int(row[5])
        hold = int(row[2])
        DB_Temp = float(row[6])
        #print(hold)
        
    except:
        print("DB Error in update_from_DB")
        
        time.sleep(1)
    
    current_temp.set (str("Current Temp is: ")+str(DB_Temp)+" "+chr(176)+" F - "+str("Set Temp is: ")+str(set_Temp)+chr(176)+" F ")
    title_var.set ("Raspberry Pi Home Thermostat - Zone - "+"Living")    ## Change to var when SQL above uses var for zone
    if (hold == 1):
        hold_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
        hold_button_txt.set(str("Held @ ")+str(hold_Temp))
    else:
        hold_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
        hold_button_txt.set(str("Hold"))
    root.after(400, update_from_DB)


# create all of the main containers
top_frame = Frame(root, bg='black', width=800, height=100, pady=3)
center = Frame(root, bg='gray2', width=800, height=200, padx=3, pady=3)
btm_frame = Frame(root, bg='white', width=800, height=80, pady=3)
btm_frame2 = Frame(root, bg='lavender', width=800, height=80, pady=3)

# layout all of the main containers
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

top_frame.grid(row=0, sticky="ew")
top_frame.grid_columnconfigure(1, weight=1)
center.grid(row=1, sticky="nsew")
btm_frame.grid(row=3, sticky="ew")
btm_frame2.grid(row=4, sticky="ew")


# create the center widgets
center.grid_rowconfigure(0, weight=1)
center.grid_columnconfigure(1, weight=1)

ctr_left = Frame(center, bg='black', width=200, height=200)
ctr_mid = Frame(center, bg='yellow', width=400, height=200, padx=3, pady=3)
ctr_right = Frame(center, bg='green', width=200, height=200, padx=3, pady=3)
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
current_temp.set (str("Current Temp is: ")+str(DB_Temp)+" "+chr(176)+str("Set Temp is: ")+str(DB_set_temp))
temp_label.grid(column=1, row=1)

## Temp Control Buttons

up = Button(ctr_left, text="Temp UP",command=temp_up, width=15,height=3, padx=3, bg="black", fg="white", activebackground="black", activeforeground="white")
down = Button(ctr_left, text="Temp Down", command=temp_down, width=15, height=3, padx=3, bg="black", fg="white", activebackground="black", activeforeground="white")
down.pack(side=BOTTOM)
up.pack(side=BOTTOM)


## Exit Button

close = Button(top_frame, text="Exit", command=end, height=2, width=10)

close.grid(row=1, column=3, sticky=E)

## Hold Button

hold_button_txt = StringVar()
hold_button_txt.set(str("Hold"))
hold_button = Button(ctr_mid, textvariable=hold_button_txt, width=15,height=3, padx=3, command=lambda: keypad("hold"), bg="black", fg="white", activebackground="black", activeforeground="white")
hold_button.grid(row=1, column=1)

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
