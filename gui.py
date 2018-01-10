from tkinter import *
import sqlite3 as lite
import time
GUI = 1
set_Temp = 0

## Window Config ##

win = Tk()
win.geometry('800x480')
win.attributes('-fullscreen', True)
header = Frame(win, bg="black")

temp_control = Frame(win,width=800, bg="green")


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
    win.destroy()
    
def update_from_DB():
    ## Keep Data Current from DB
    global set_Temp
    global backup_Temp
    global end_Thread
    global hold_Temp
    global temp_overriden
    global last_motion
    global hold
    try:
        conn = lite.connect('thermostat.db')
        c = conn.cursor()
        c.execute("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion FROM settings WHERE zone = 'living'")
        row = c.fetchone()
        # Store Data from DB
        set_Temp = float(row[0])
        backup_Temp = float(row[1])
        hold_Temp = int(row[3])
        last_motion = int(row[4])
        motion = int(row[5])
        hold = int(row[2])
        #print("Connected")
    except:
        print("DB Error in update_from_DB")
        
        time.sleep(1)
    temp.configure(text=set_Temp)     
    win.after(400, update_from_DB)
    
## GUI Widgets ##

up = Button(temp_control, text="Temp UP",command=temp_up, height=5, width=10)
down = Button(temp_control, text="Temp Down", command=temp_down, height=5, width=10)
close = Button(header, text="Exit", command=end, height=5, width=5)
temp = Label(temp_control, text=0, width=5)

close.grid(column=4, row=5)
up.grid(column=0, row=5)
down.grid(column=0, row=6)
temp.grid(column=1, row=5)
header.pack(side=TOP)
temp_control.pack(side=BOTTOM)

## Run Window ##


win.after(1000, update_from_DB)
win.mainloop()
