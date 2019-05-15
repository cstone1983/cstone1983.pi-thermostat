from tkinter import *
import time
import MySQLdb
from datetime import datetime

selected_zone = 'Living'
show_zone = ('Zone:\n'+selected_zone)
def end(): ## EXIT GUI
    root.destroy()
def select_zone(zone):
    global selected_zone
    selected_zone = zone
    show_zone = ('Zone:\n'+selected_zone)
    current_zone.set (show_zone)
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
        
def clock():
    global selected_zone
    global timer
    global active
    now = int(time.time())
    if (selected_zone == 'Living'):
        timer = 0
        active = now
    if ((selected_zone != 'Living') & (timer==0)):
        timer = 1
        active = int(time.time())
    if ((selected_zone != 'Living') & (timer==1) & (now > (active+20))):
        select_zone('Living')
        timer = 0
        
    time_string = time.strftime('%A \n%-I:%M %p')
    time_current.set(str(time_string))
    root.after(100, clock) # run itself again after 1000 ms
    
def update_from_DB():
    ## Keep Data Current from DB
    global selected_zone
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
        sql = ("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion, temp , relay , humidity FROM settings WHERE zone = '" + str(selected_zone) + "'")
        c.execute(sql)
        row = c.fetchone()
        # Store Data from DB
        DB_set_Temp = float(row['settemp'])
        backup_Temp = float(row['backuptemp'])
        hold_Temp = int(row['holdtemp'])
        hold = int(row['hold'])
        DB_Temp = float(row['temp'])
        DB_relay = float(row['relay'])
        DB_humidity = float(row['humidity'])        
        
    except:
        print("DB Error in update_from_DB")
        time.sleep(.2)
    
    
    set_temp.set (str("Set Temp is: ")+str(DB_set_Temp)+" "+degree_sign+" F - "+(str(DB_humidity) + " %"))
    current_temp.set(str(DB_Temp)+degree_sign+" F ")
    
    if (hold == 1):
        hold_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
        hold_button_txt.set(str("Held @ ")+str(hold_Temp))
    else:
        hold_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
        hold_button_txt.set(str("Hold"))

    if DB_relay == 1:
        temp_label.configure(fg="green")
        
    elif DB_relay == 0:
        temp_label.configure(fg="white")
    if (sql_fetch("hold", "Control") == 1):
        away_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
    if (sql_fetch("hold", "Control") == 0):
        away_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
    root.after(400, update_from_DB)

def Info_Update():
    ##Living Update
    z1_set = sql_fetch("settemp", "living")
    z1_temp = sql_fetch("temp", "living")
    z1_relay = sql_fetch("relay", "living")
    z1_active = sql_fetch("active", "living")
    ##Kitchen Update
    z2_set = sql_fetch("settemp", "kitchen")
    z2_temp = sql_fetch("temp", "kitchen")
    z2_relay = sql_fetch("relay", "kitchen")
    z2_active = sql_fetch("active", "kitchen")
    ##Upstairs Update
    z3_set = sql_fetch("settemp", "upstairs")
    z3_temp = sql_fetch("temp", "upstairs")
    z3_relay = sql_fetch("relay", "upstairs")
    z3_active = sql_fetch("active", "upstairs")
    ##Control
    z4_active = sql_fetch("active", "control")
    z4_hold = sql_fetch("hold", "control")
    
    living_temp.set (str("Living:\nSet: " + str(z1_set) + "\nTemp:\n" + str(z1_temp) +degree_sign))
    kitchen_temp.set (str("Kitchen:\nSet: " + str(z2_set) + "\nTemp:\n" + str(z2_temp) +degree_sign))
    upstairs_temp.set (str("Upstairs:\nSet: " + str(z3_set) + "\nTemp:\n" + str(z3_temp) +degree_sign))
    if z1_relay == 1:
        living_label.configure(fg="green")
    elif z1_relay == 0:
        living_label.configure(fg="white")
    if z2_relay == 1:
        kitchen_label.configure(fg="green")
    elif z2_relay == 0:
        kitchen_label.configure(fg="white")
        
    if z3_relay == 1:
        upstairs_label.configure(fg="green")
    elif z3_relay == 0:
        upstairs_label.configure(fg="white")
        
    if(z2_active == 0):
        kitchen_label.configure(fg="red")
    if(z3_active == 0):
        upstairs_label.configure(fg="red")
    if(z4_active == 0):
        control_label.configure(fg="red")
        control_temp.set (str("Control\nOffline"))
    if(z4_active == 1):
        control_label.configure(fg="white")
        control_temp.set (str("Control\nOnline"))
    if(z4_hold == 1):
        away_button.configure(bg="red")
    root.after(100, Info_Update) # run itself again after 1000 ms
def keypad(field):
    global selected_zone
    global pin
    global keyp
    global active
    # Setup DB Connection
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    hold = sql_fetch("hold", selected_zone)
    def code(value): #Run after each keypress
        global keyp
        global pin
        
        if value == '<--':# remove last number
            pin = pin[:-1]
            e.delete('0', 'end')
            e.insert('end', pin)
            active = int(time.time())
        elif value == 'Set':
            # check Temp
            active = int(time.time())
            if (int(pin) > 49 and int(pin) < 76):
                print("Temp OK")
                try:
                    sql = """UPDATE settings SET holdtemp = %s WHERE zone = %s"""
                    val = (pin, selected_zone)
                    c.execute(sql, val)
                    conn.commit()
                    hold = 1
                    sql = """UPDATE settings SET hold = %s WHERE zone = %s"""
                    val = (hold, selected_zone)
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
            active = int(time.time())
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
            
        active = int(time.time())
        hold = 0
        sql = ("""UPDATE settings SET hold = %s WHERE zone = %s""")
        val = (hold, selected_zone)
        c.execute(sql, val)
        conn.commit()

def away(): #Hold temp while out of house. eleminate dog setting motion off
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    home_away = sql_fetch("hold", "Control")
    if (home_away == 0):
        try:
            sql_update("holdtemp", 58, "Living", "Setting Home AWAY")
            sql_update("settemp", 58, "Upstairs", "Setting Home AWAY")
            sql_update("settemp", 58, "Kitchen", "Setting Home AWAY")
            sql_update("hold", 1, "Living", "Setting Home AWAY")
            sql_update("hold", 1, "Control", "Setting Home AWAY")
        except:
            print("Error Updating DB")
    if (home_away == 1):
        try:
            sql_update("hold", 0, "Living", "Setting Home AWAY")
            sql_update("settemp", 62, "Kitchen", "Setting Home AWAY")
            sql_update("settemp", 58, "Upstairs", "Setting Home AWAY")
            sql_update("hold", 0, "Control", "Setting Home AWAY")
        except:
            print("Error Updating DB")
def temp_up():
    global selected_zone
    global acive
    active = int(time.time())
    set_Temp = sql_fetch("settemp", selected_zone)
    new_temp = set_Temp + 1
    sql_update("settemp", new_temp, selected_zone, "Temp UP")
    
def temp_down():
    global selected_zone
    global acive
    active = int(time.time())
    set_Temp = sql_fetch("settemp", selected_zone)
    new_temp = set_Temp - 1
    sql_update("settemp", new_temp, selected_zone, "Temp UP")
def kids_bed():
    ## Chagne to pull vars from db
    global selected_zone
    global acive
    active = int(time.time())
    sql_update("settemp", 61, "kitchen", "Kids Bedtime")
    sql_update("settemp", 61, "upstairs", "Kids Bedtime")
def night():
    ## Change to pull vars from db...
    global selected_zone
    global acive
    active = int(time.time())
    sql_update("settemp", 61, "kitchen", "Night Shutdown")
    sql_update("holdtemp", 61, "living", "Night Shutdown")
    sql_update("hold", 1, "living", "Night Shutdown")
    sql_update("settemp", 61, "upstairs", "Night Shutdown")
    
def morning():
    global selected_zone
    global acive
    active = int(time.time())
    sql_update("settemp", 62, "kitchen", "Kids Bedtime")
    sql_update("hold", 0, "living", "Kids Bedtime")
    sql_update("settemp", 58, "upstairs", "Kids Bedtime")
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


root = Tk()
root.attributes("-fullscreen", True)
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
degree_sign= u'\N{DEGREE SIGN}'
pixel = PhotoImage()

##Main Frames
Header = Frame(root, height=131, width=800, bg="black")
Center = Frame(root, height=285, width=800, bg="black")
Footer = Frame(root, height=65, width=800, bg="red")

##Sub Frames
#Header
Zone = Frame(Header, height=131, width=195, bg="black")
Time = Frame(Header, height=131, width=410, bg="black")
Exit = Frame(Header, height=131, width=195, bg="black")
#Center
Info = Frame(Center, height=285, width=120, bg="black")
Status = Frame(Center, height=285, width=435, bg="black")
Mode = Frame(Center, height=285, width=195, bg="black")

## Place Frames
#Main Frames
Header.grid(column=0, row=0, sticky=NSEW)
Center.grid(column=0, row=1, sticky=NSEW)
#Center.grid_columnconfigure(1, minsize=428.75)
Footer.grid(column=0, row=2, sticky=NSEW)
#Header Frames
Zone.grid(column=0, row=0)
Time.grid(column=1, row=0)
Time.grid_columnconfigure(0, minsize=410)
Zone.grid_columnconfigure(0, minsize=195)
Exit.grid(column=2, row=0)
Exit.grid_columnconfigure(2, minsize=195)
#Center Frames
Info.grid(column=0, row=0, sticky=W)
Info.grid_columnconfigure(0, weight=1, minsize=120)
Status.grid(column=1, row=0)
Status.grid_columnconfigure(1, minsize=175,weight=1)
Status.grid_columnconfigure(0, minsize=260,weight=1)
Mode.grid(column=2, row=0, sticky=E)

#### Header Panel #####
## Zone Panel
#Selected Zone

current_zone = StringVar()
current_zone_label = Label(Zone, textvariable=current_zone, font=("Helvetica 24"), bg = "black", fg="white")
current_zone.set (show_zone)
current_zone_label.grid(column=0, row=0)

#Date/Time

time_current=StringVar()
time_string = time.strftime('%A \n%-I:%M %p')
time_current.set(str(time_string))
time_current_label= Label(Time,  textvariable=time_current, font=("Helvetica 40"), bg = "black", fg="white")
time_current_label.grid(column=0, row=0)
#Exit Panel
#Exit Button
exit_button_txt = StringVar()
exit_button_txt.set(str("Exit"))
exit_button = Button(Exit, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=exit_button_txt, command=end, bg="black", fg="red", activebackground="black", activeforeground="red",compound="right")
exit_button.config(height=100, width=200)
exit_button.grid(column=1, row=1)


##### Center Panel ######
## Info
## Living rm Temp
living_temp = StringVar()
living_label = Label(Info, textvariable=living_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
living_temp.set (str("Living:\nSet:\n62\nT:\n64")+degree_sign)
living_label.grid(column=0, row=0)
## kitche Temp
kitchen_temp = StringVar()
kitchen_label = Label(Info, textvariable=kitchen_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
kitchen_temp.set (str("   62")+degree_sign)
kitchen_label.grid(column=0, row=1)
## upstairs Temp
upstairs_temp = StringVar()
upstairs_label = Label(Info, textvariable=upstairs_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
upstairs_temp.set (str("   62")+degree_sign)
upstairs_label.grid(column=0, row=2)
## control info
control_temp = StringVar()
control_label = Label(Info, textvariable=control_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
control_temp.set (str("Control\nOnline"))
control_label.grid(column=0, row=3)
## Set Temp ##
set_temp = StringVar()
set_temp_label = Label(Status, textvariable=set_temp, font=("Helvetica 19"), bg = "black", fg="white")
set_temp.set (str("62")+degree_sign)
set_temp_label.grid(column=0, row=0, columnspan=2)
## Current Temp
current_temp = StringVar()
temp_label = Label(Status, textvariable=current_temp, font=("Helvetica 35 bold"), bg = "black", fg="white")
current_temp.set (str("   62")+degree_sign)
temp_label.grid(column=0, row=1, rowspan=2, sticky=E)

## Temp UP

temp_up_button_txt = StringVar()
temp_up_button_txt.set(str("Temp UP"))
temp_up_button = Button(Status, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=temp_up_button_txt, command=temp_up, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
temp_up_button.config(height=100, width=200)
temp_up_button.grid(column=1, row=1, sticky=E)

## Temp Down

temp_down_button_txt = StringVar()
temp_down_button_txt.set(str("Temp Down"))
temp_down_button = Button(Status, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=temp_down_button_txt, command=temp_down, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
temp_down_button.config(height=100, width=200)
temp_down_button.grid(column=1, row=2)



##### Mode Panel #####
## Away Button
away_button_txt = StringVar()
away_button_txt.set(str("Away"))
away_button = Button(Mode, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=away_button_txt, command=away, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
away_button.config(height=61, width=195)
away_button.grid(column=0, row=0, sticky=N)

## Hold Button

hold_button_txt = StringVar()
hold_button_txt.set(str("Hold"))
hold_button = Button(Mode, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=hold_button_txt, command=lambda: keypad("hold"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
hold_button.config(height=61, width=195)
hold_button.grid(column=0, row=1)

## Morning Button

morning_button_txt = StringVar()
morning_button_txt.set(str("Morning"))
morning_button = Button(Mode, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=morning_button_txt, command=morning, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
morning_button.config(height=61, width=195)
morning_button.grid(column=0, row=2)

## Night Button

night_button_txt = StringVar()
night_button_txt.set(str("Night"))
night_button = Button(Mode, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=night_button_txt, command=night, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
night_button.config(height=61, width=195)
night_button.grid(column=0, row=3, sticky=S)

######## Footer Panel ######

## History Button

history_button_txt = StringVar()
history_button_txt.set(str("History"))
history_button = Button(Footer, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=history_button_txt, command=end, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
history_button.config(height=61, width=135)
history_button.grid(column=0, row=0)

## Living Room Button

living_button_txt = StringVar()
living_button_txt.set(str("Living"))
living_button = Button(Footer, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=living_button_txt, command=lambda: select_zone("Living"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
living_button.config(height=61, width=135)
living_button.grid(column=1, row=0)

## Kitchen Button

kitchen_button_txt = StringVar()
kitchen_button_txt.set(str("Kitchen"))
kitchen_button = Button(Footer, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=kitchen_button_txt, command=lambda: select_zone("Kitchen"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
kitchen_button.config(height=61, width=135)
kitchen_button.grid(column=2, row=0)

## Upstairs Button

upstairs_button_txt = StringVar()
upstairs_button_txt.set(str("Upstairs"))
upstairs_button = Button(Footer, image=pixel, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=upstairs_button_txt, command=lambda: select_zone("Upstairs"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
upstairs_button.config(height=61, width=135)
upstairs_button.grid(column=3, row=0)

## Kids Bed

kids_button_txt = StringVar()
kids_button_txt.set(str("Kids Bedtime"))
kids_button = Button(Footer, image=pixel, font="Verdana 17", highlightthickness=0, borderwidth=0, textvariable=kids_button_txt, command=kids_bed, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
kids_button.config(height=61, width=140)
kids_button.grid(column=4, row=0)

clock()
Info_Update()
root.after(1000, update_from_DB)
root.mainloop()
