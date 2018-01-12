from tkinter import *
import sqlite3 as lite
import time
GUI = 1
set_Temp = 0
global DB_Temp
DB_Temp = 0
global DB_set_temp
DB_set_temp = 0
root = Tk()
root.title('Model Definition')
root.geometry('{}x{}'.format(800, 480))


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
        #print("Connected")
        
    except:
        print("DB Error in update_from_DB")
        
        time.sleep(1)
    
    current_temp.set (str("Current Temp is: ")+str(DB_Temp))
    set_temp.set (str("Temp Set at: ")+str(set_Temp))
    root.after(400, update_from_DB)


# create all of the main containers
top_frame = Frame(root, bg='cyan', width=800, height=50, pady=3)
center = Frame(root, bg='gray2', width=50, height=40, padx=3, pady=3)
btm_frame = Frame(root, bg='white', width=450, height=45, pady=3)
btm_frame2 = Frame(root, bg='lavender', width=450, height=60, pady=3)

# layout all of the main containers
root.grid_rowconfigure(1, weight=1)
root.grid_columnconfigure(0, weight=1)

top_frame.grid(row=0, sticky="ew")
center.grid(row=1, sticky="nsew")
btm_frame.grid(row=3, sticky="ew")
btm_frame2.grid(row=4, sticky="ew")


# create the center widgets
center.grid_rowconfigure(0, weight=1)
center.grid_columnconfigure(1, weight=1)

ctr_left = Frame(center, bg='blue', width=100, height=190)
ctr_mid = Frame(center, bg='yellow', width=250, height=190, padx=3, pady=3)
ctr_right = Frame(center, bg='green', width=100, height=190, padx=3, pady=3)

ctr_left.grid(row=0, column=0, sticky="ns")
ctr_mid.grid(row=0, column=1, sticky="nsew")
ctr_right.grid(row=0, column=2, sticky="ns")

#### Status Lables


## Zone Selection

zone = StringVar(top_frame)
zone="Living"
option = OptionMenu(top_frame, zone, "one", "two", "three", "four")
option.grid(row=1, column=0)

##Current Temp

current_temp = StringVar()

temp_label = Label(top_frame, textvariable=current_temp,text="Helvetica", font=("Helvetica", 16), bg = "yellow")
current_temp.set (str("Current Temp is: ")+str(DB_Temp))
temp_label.grid(column=1, row=1)

set_temp = StringVar()

set_temp_label = Label(top_frame, textvariable=set_temp,text="Helvetica", font=("Helvetica", 16), bg = "yellow")
set_temp.set (str("Set Temp is: ")+str(DB_set_temp))
set_temp_label.grid(column=2, row=1)

## Temp Control Buttons

up = Button(ctr_left, text="Temp UP",command=temp_up, width=10,height=2, padx=3)
down = Button(ctr_left, text="Temp Down", command=temp_down, width=10, height=2, padx=3)

up.pack(side=BOTTOM)
down.pack(side=BOTTOM)

## Exit Button

close = Button(top_frame, text="Exit", command=end, height=2, width=10)

close.grid(row=1, column=3, sticky=E, padx=1)



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
