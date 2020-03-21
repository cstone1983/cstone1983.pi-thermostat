import tkinter as tk
import time
import MySQLdb
from datetime import datetime

class GUI():

    def __init__(self, master):
       self.master = master
       self.master.attributes("-fullscreen", True)
       self.screen_width = master.winfo_screenwidth()
       self.screen_height = master.winfo_screenheight()
       self.degree_sign= u'\N{DEGREE SIGN}'
       self.selected_zone = 'Living'
       self.a_timeout = 10 ## Seconds for activity timeout
       self.a_timer = time.time() ## Set timer for GUI acivity (return to Living after certin time)
       ## Setup DB Connection Vars
       self.host = "localhost"
       self.username = "pi"
       self.password = "python"
       self.database = "thermostat"
       self.settings = Settings
       ## tkinter methods for setting up GUI
       self.layout_set() 
       self.panel_header() 
       self.panel_center()
       self.panel_footer()
       
       ##Continuiously running methods for updates
       self.clock()
       self.update()
          
    def layout_set(self):
        ##Main Frames
        self.Header = tk.Frame(self.master, height=(self.screen_height * .25), width=self.screen_width, bg="black")
        self.Center = tk.Frame(self.master, height=(self.screen_height * .5), width=self.screen_width, bg="black")
        self.Footer = tk.Frame(self.master, height=(self.screen_height * .25), width=self.screen_width, bg="black")

        ##Sub Frames
        #Header
        self.Zone = tk.Frame(self.Header, height=(self.screen_height * .25), width=(self.screen_width * .25), bg="black")
        self.Time = tk.Frame(self.Header, height=(self.screen_height * .25), width=(self.screen_width * .5), bg="black")
        self.Exit = tk.Frame(self.Header, height=(self.screen_height * .25), width=(self.screen_width * .25), bg="black")
        #Center
        self.Info = tk.Frame(self.Center, height=(self.screen_height * .5), width=(self.screen_width * .2), bg="black")
        self.Status = tk.Frame(self.Center, height=(self.screen_height * .5), width=(self.screen_width * .6), bg="black")
        self.Mode = tk.Frame(self.Center, height=(self.screen_height * .5), width=(self.screen_width * .2), bg="black")

        ## Place Frames
        #Main Frames
        self.Header.grid(column=0, row=0)
        self.Center.grid(column=0, row=1)
        self.Footer.grid(column=0, row=2, sticky='nsew')
        #Header Frames
        self.Zone.grid(column=0, row=0)
        self.Time.grid(column=1, row=0)
        self.Exit.grid(column=2, row=0)
        self.Time.grid_columnconfigure(0, minsize=(self.screen_width * .5))
        self.Zone.grid_columnconfigure(0, minsize=(self.screen_width * .25))
        self.Exit.grid_columnconfigure(0, minsize=(self.screen_width * .25))
        
        #Center Frames
        self.Status.grid_columnconfigure(0, minsize=(self.screen_width * .3))
        self.Status.grid_columnconfigure(1, minsize=(self.screen_width * .3))
        self.Mode.grid_columnconfigure(0, minsize=(self.screen_width * .2))
        self.Info.grid_columnconfigure(0, weight=1, minsize=(self.screen_width * .2))
        self.Info.grid(column=0, row=0)
        self.Status.grid(column=1, row=0)
        self.Mode.grid(column=2, row=0)
        
        ##Footer
        
        self.Footer.grid_rowconfigure(0, weight=1)
    def panel_header(self):
        #### Header Panel #####
        
        ## Zone Panel
        #Selected Zone
        self.show_zone = ('Zone:\n'+self.selected_zone)
        
        self.current_zone = tk.StringVar()
        current_zone_label = tk.Label(self.Zone, padx=10, textvariable=self.current_zone, font=("Helvetica 24"), bg = "black", fg="white").grid(column=0, row=0)
        self.current_zone.set (self.show_zone)
        
        #Date/Time
        
        self.time_current= tk.StringVar()
        self.time_string = time.strftime('%A \n%-I:%M %p')
        self.time_current.set(str(self.time_string))
        self.time_current_label= tk.Label(self.Time,  textvariable=self.time_current, font=("Helvetica 40"), bg = "black", fg="white").grid(column=0, row=0)
        
        ##Exit Panel
        #Exit Button
        exit_button_txt = tk.StringVar()
        exit_button_txt.set(str("Exit"))
        exit_button = tk.Button(self.Exit, font="Verdana 40", highlightthickness=0, borderwidth=0, textvariable=exit_button_txt, command=self.exit, bg="black", fg="red", activebackground="black", activeforeground="red")
        exit_button.grid(column=0, row=0, sticky="nsew")

    def panel_center(self):

        ##### Center Panel ######
        ## Info
        ## Living rm Temp
        self.living_temp = tk.StringVar()
        self.living_label = tk.Label(self.Info, textvariable=self.living_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
        self.living_temp.set (str("Living:\nSet:\n62\nT:\n64")+self.degree_sign)
        self.living_label.grid(column=0, row=0)
        self.living_label.bind("<Button-1>", lambda a="living": self.select_zone("Living"))
        ## kitche Temp
        self.kitchen_temp = tk.StringVar()
        self.kitchen_label = tk.Label(self.Info, textvariable=self.kitchen_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
        self.kitchen_temp.set (str("   62")+self.degree_sign)
        self.kitchen_label.grid(column=0, row=1)
        self.kitchen_label.bind("<Button-1>", lambda a="living": self.select_zone("Kitchen"))
        ## upstairs Temp
        self.upstairs_temp = tk.StringVar()
        self.upstairs_label = tk.Label(self.Info, textvariable=self.upstairs_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
        self.upstairs_temp.set (str("   62")+self.degree_sign)
        self.upstairs_label.grid(column=0, row=2)
        self.upstairs_label.bind("<Button-1>", lambda a="living": self.select_zone("Upstairs"))
        ## control info
        self.control_temp = tk.StringVar()
        self.control_label = tk.Label(self.Info, textvariable=self.control_temp, font=("Helvetica 12 bold"), bg = "black", fg="white")
        self.control_temp.set (str("Control\nOnline"))
        self.control_label.grid(column=0, row=3)
        ## Set Temp ##
        self.set_temp = tk.StringVar()
        self.set_temp_label = tk.Label(self.Status, textvariable=self.set_temp, font=("Helvetica 19"), bg = "black", fg="white")
        self.set_temp.set (str("62")+self.degree_sign)
        self.set_temp_label.grid(column=0, row=0, columnspan=2)
        ## Current Temp
        self.current_temp = tk.StringVar()
        self.temp_label = tk.Label(self.Status, textvariable=self.current_temp, font=("Helvetica 35 bold"), bg = "black", fg="white")
        self.current_temp.set (str("   62")+self.degree_sign)
        self.temp_label.grid(column=0, row=1, rowspan=2)
        
        ## Temp UP
        
        temp_up_button_txt = tk.StringVar()
        temp_up_button_txt.set(str("Temp UP"))
        self.temp_up_button = tk.Button(self.Status, font="Verdana 24", highlightthickness=0, borderwidth=0, textvariable=temp_up_button_txt, command=self.temp_up, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.temp_up_button.config(height=3)
        self.temp_up_button.grid(column=1, row=1)
        
        ## Temp Down
        
        temp_down_button_txt = tk.StringVar()
        temp_down_button_txt.set(str("Temp Down"))
        self.temp_down_button = tk.Button(self.Status, font="Verdana 24", highlightthickness=0, borderwidth=0, textvariable=temp_down_button_txt, command=self.temp_down, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.temp_down_button.config(height=3)
        self.temp_down_button.grid(column=1, row=2)
        
        
        
        ##### Mode Panel #####
        ## Away Button
        self.away_button_txt = tk.StringVar()
        self.away_button_txt.set(str("Away"))
        self.away_button = tk.Button(self.Mode, font="Verdana 24", highlightthickness=0, borderwidth=0, textvariable=self.away_button_txt, command=self.away, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.away_button.config(height=2)
        self.away_button.grid(column=0, row=0, sticky='nsew')
        
        ## Hold Button
        
        self.hold_button_txt = tk.StringVar()
        self.hold_button_txt.set(str("Hold"))
        self.hold_button = tk.Button(self.Mode, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.hold_button_txt, command=self.hold, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.hold_button.config(height=2)
        self.hold_button.grid(column=0, row=1, sticky='nsew')
        
        ## Day Button
        
        self.day_button_txt = tk.StringVar()
        self.day_button_txt.set(str("Day"))
        self.day_button = tk.Button(self.Mode, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.day_button_txt, command=self.day, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.day_button.config(height=2)
        self.day_button.grid(column=0, row=2, sticky='nsew')
        
        ## Night Button
        
        self.night_button_txt = tk.StringVar()
        self.night_button_txt.set(str("Night"))
        self.night_button = tk.Button(self.Mode, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.night_button_txt, command=self.night, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.night_button.config(height=2)
        self.night_button.grid(column=0, row=3, sticky='nsew')
    def panel_footer(self):
        ######## Footer Panel ######
        
        ## History Button
        
        self.history_button_txt = tk.StringVar()
        self.history_button_txt.set(str("History"))
        self.history_button = tk.Button(self.Footer, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.history_button_txt, command= lambda: self.settings(self.settings), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.history_button.config(height=2, width=9)
        self.history_button.grid(column=0, row=0)
        
        ## Living Room Button
        
        self.living_button_txt = tk.StringVar()
        self.living_button_txt.set(str("Living"))
        self.living_button = tk.Button(self.Footer, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.living_button_txt, command=lambda: self.select_zone("Living"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.living_button.config(height=2, width=8)
        self.living_button.grid(column=1, row=0)
        
        ## Kitchen Button
        
        self.kitchen_button_txt = tk.StringVar()
        self.kitchen_button_txt.set(str("Kitchen"))
        self.kitchen_button = tk.Button(self.Footer, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.kitchen_button_txt, command=lambda: self.select_zone("Kitchen"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.kitchen_button.config(height=2, width=8)
        self.kitchen_button.grid(column=2, row=0)
        
        ## Upstairs Button
        
        self.upstairs_button_txt = tk.StringVar()
        self.upstairs_button_txt.set(str("Upstairs"))
        self.upstairs_button = tk.Button(self.Footer, font="Verdana 19", highlightthickness=0, borderwidth=0, textvariable=self.upstairs_button_txt, command=lambda: self.select_zone("Upstairs"), bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        self.upstairs_button.config(height=2, width=8)
        self.upstairs_button.grid(column=3, row=0)
        
        ## Kids Bed
        
        self.kids_button_txt = tk.StringVar()
        self.kids_button_txt.set(str("Kids Bedtime"))
        self.kids_button = tk.Button(self.Footer, font="Verdana 17", highlightthickness=0, borderwidth=0, textvariable=self.kids_button_txt, command=self.kids_bed, bg="black", fg="white", activebackground="black", activeforeground="white",compound="right")
        #self.kids_button.config(height=2, width=10)
        self.kids_button.grid(column=4, row=0, sticky='ew')



    def clock(self):            
        time_string = time.strftime('%A \n%-I:%M %p')
        self.time_current.set(str(time_string))
        now = time.time()
        
        ## Activity Timer 
        if (now > (self.a_timer + self.a_timeout)):
            self.select_zone("Living")
        
        self.master.after(100, self.clock) # run itself again after 1000 ms
    def activity(self):
        ## Reset Update timer to now
        self.a_timer = time.time()
    
    def exit(self):
        ##Exit GUI
        self.master.destroy()     
        
    def settings(self, _class):
        self.settings_win = tk.Toplevel(self.master)
        _class(self.settings_win)
           
    
    def temp_up(self):
        ## Increase temp by 1 in DB
        set_Temp = self.sql_fetch("settemp", self.selected_zone)
        new_temp = set_Temp + 1
        self.sql_update("settemp", new_temp, self.selected_zone, "Temp UP")
        
        self.activity()
                
    def temp_down(self):
        set_Temp = self.sql_fetch("settemp", self.selected_zone)
        new_temp = set_Temp - 1
        self.sql_update("settemp", new_temp, self.selected_zone, "Temp UP")
        self.activity()
    def day(self):
        ## Set Temps for moring ( need to change to Mode and move temps to DB)
        self.sql_update("settemp", 62, "kitchen", "Kids Bedtime")
        self.sql_update("hold", 0, "living", "Kids Bedtime")
        self.sql_update("settemp", 58, "upstairs", "Kids Bedtime")
        self.activity()
    def night(self):
        self.sql_update("settemp", 61, "kitchen", "Night Shutdown")
        self.sql_update("holdtemp", 61, "living", "Night Shutdown")
        self.sql_update("hold", 1, "living", "Night Shutdown")
        self.sql_update("settemp", 61, "upstairs", "Night Shutdown")    
        self.activity()
    def kids_bed(self):
        self.sql_update("settemp", 61, "kitchen", "Kids Bedtime")
        self.sql_update("settemp", 61, "upstairs", "Kids Bedtime")
        self.activity()
    def select_zone(self, zone):
        show_zone = ('Zone:\n'+str(zone))
        self.current_zone.set (show_zone)
        self.selected_zone = zone
        #self.update_now()
        self.activity()
    def sql_fetch(self, field, zone):
        ## Connect to SQL DB
        try:
            conn = MySQLdb.connect(self.host,self.username,self.password,self.database, port=3306 )
            c = conn.cursor (MySQLdb.cursors.DictCursor)
            sql = ("SELECT " + str(field) + " FROM settings WHERE zone = '" + str(zone) + "'")
            c.execute(sql)
            row = c.fetchone()
            return(row[field])
        except:
            error = ("Error in SQL Update - ")
            self.log("error")

    def sql_update(self, field, value, zone, msg):
        ## Connect to SQL DB
        try:
            conn = MySQLdb.connect(self.host,self.username,self.password,self.database, port=3306 )
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
            self.log(error)
    def door_lock_mode(self, mode):
        ## Connect to SQL DB
        try:
            conn = MySQLdb.connect(self.host,self.username,self.password,"doorlock", port=3306 )
            c = conn.cursor (MySQLdb.cursors.DictCursor)
        except:
            log("Error Connecting to DB")
        ## Create SQL and Update settings table
        try:
            sql = ("UPDATE settings SET mode = '" + str(mode) + "' WHERE door = 'Front'")
            c.execute(sql)
            conn.commit()
            #log(("Changed " + str(field) + " to " + str(value) + " for zone " + str(zone)))
        except:
            error = ("Error in SQL Update - " + msg)
            self.log(error)    
        
    def away(self):
        conn = MySQLdb.connect(self.host,self.username,self.password,self.database, port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)
        home_away = self.sql_fetch("hold", "Control")
        if (home_away == 0):
            try:
                self.sql_update("holdtemp", 58, "Living", "Setting Home AWAY")
                self.sql_update("settemp", 58, "Upstairs", "Setting Home AWAY")
                self.sql_update("settemp", 58, "Kitchen", "Setting Home AWAY")
                self.sql_update("hold", 1, "Living", "Setting Home AWAY")
                self.sql_update("hold", 1, "Control", "Setting Home AWAY")
                self.door_lock_mode(4)
            except:
                print("Error Updating DB")
        if (home_away == 1):
            try:
                self.sql_update("hold", 0, "Living", "Setting Home AWAY")
                self.sql_update("settemp", 62, "Kitchen", "Setting Home AWAY")
                self.sql_update("settemp", 58, "Upstairs", "Setting Home AWAY")
                self.sql_update("hold", 0, "Control", "Setting Home AWAY")
                self.door_lock_mode(0)
            except:
                print("Error Updating DB")

    def hold(self):
        global selected_zone
        global pin
        global keyp
        global active
        # Setup DB Connection
        conn = MySQLdb.connect(self.host,self.username,self.password,self.database, port=3306 )
        c = conn.cursor (MySQLdb.cursors.DictCursor)
        hold = self.sql_fetch("hold", self.selected_zone)
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
                        val = (pin, self.selected_zone)
                        c.execute(sql, val)
                        conn.commit()
                        hold = 1
                        sql = """UPDATE settings SET hold = %s WHERE zone = %s"""
                        val = (hold, self.selected_zone)
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
    
            keyp = tk.Tk()
            keyp.title('Enter ' + "hold" + ' Value')
            keyp.geometry('{}x{}'.format(800, 480))
            keyp.configure(bg="black")
            # place to display pin
            e = tk.Entry(keyp)
            e.grid(row=0, column=0, columnspan=3, ipady=5)
    
            # create buttons using `keys`
            for y, row in enumerate(keys, 1):
                for x, key in enumerate(row):
                    # `lambda` inside `for` has to use `val=key:code(val)` 
                    # instead of direct `code(key)`
                    b = tk.Button(keyp, text=key, width=3, height=3, font=("Helvetica", 14), bg="black", fg="white", activebackground="black", activeforeground="white", command=lambda val=key:code(val))
                    b.grid(row=y, column=x, ipadx=10, ipady=10)
    
            keyp.mainloop()
        else: # If hold is already set...Clear Hold
                
            active = int(time.time())
            hold = 0
            sql = ("""UPDATE settings SET hold = %s WHERE zone = %s""")
            val = (hold, self.selected_zone)
            c.execute(sql, val)
            conn.commit()
    


    def update_now(self):
        ## Keep Data Current from DB
        
        try:
            conn = MySQLdb.connect(self.host,self.username,self.password,self.database, port=3306 )
            c = conn.cursor (MySQLdb.cursors.DictCursor)
            sql = ("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion, temp , relay , humidity FROM settings WHERE zone = '" + str(self.selected_zone) + "'")
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
        
        
        self.set_temp.set (str("Set Temp is: ")+str(DB_set_Temp)+" "+srlf.degree_sign+" F - "+(str(DB_humidity) + " %"))
        self.current_temp.set(str(DB_Temp)+self.degree_sign+" F ")
        
        if (hold == 1):
            self.hold_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
            self.hold_button_txt.set(str("Held @ ")+str(hold_Temp))
        else:
            self.hold_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
            self.hold_button_txt.set(str("Hold"))
    
        if DB_relay == 1:
            self.temp_label.configure(fg="green")
            
        elif DB_relay == 0:
            self.temp_label.configure(fg="white")
        if (sql_fetch("hold", "Control") == 1):
            self.away_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
        if (sql_fetch("hold", "Control") == 0):
            self.away_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
       

    def update(self):
        ## Update data for current zone
        try:
            conn = MySQLdb.connect(self.host,self.username,self.password,self.database, port=3306 )
            c = conn.cursor (MySQLdb.cursors.DictCursor)
            sql = ("SELECT settemp, backuptemp, hold, holdtemp, lastmotion, motion, temp , relay , humidity FROM settings WHERE zone = '" + str(self.selected_zone) + "'")
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
        
        
        self.set_temp.set (str("Set Temp is: ")+str(DB_set_Temp)+" "+self.degree_sign+" F - "+(str('{0:.2f}'.format(DB_humidity)) + " %"))
        self.current_temp.set(str(DB_Temp)+self.degree_sign+" F ")
        
        if (hold == 1):
            self.hold_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
            self.hold_button_txt.set(str("Held @ ")+str(hold_Temp))
        else:
            self.hold_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
            self.hold_button_txt.set(str("Hold"))
    
        if DB_relay == 1:
            self.temp_label.configure(fg="green")
            
        elif DB_relay == 0:
            self.temp_label.configure(fg="white")
        if (self.sql_fetch("hold", "Control") == 1):
            self.away_button.configure(bg="red", fg="white", activebackground="red", activeforeground="white")
        if (self.sql_fetch("hold", "Control") == 0):
            self.away_button.configure(bg="black", fg="white", activebackground="black", activeforeground="white")
       
    
        ##Living Update
        z1_set = self.sql_fetch("settemp", "living")
        z1_temp = self.sql_fetch("temp", "living")
        z1_relay = self.sql_fetch("relay", "living")
        z1_active = self.sql_fetch("active", "living")
        z1_motion = self.sql_fetch("motion", "living")
        ##Kitchen Update
        z2_set = self.sql_fetch("settemp", "kitchen")
        z2_temp = self.sql_fetch("temp", "kitchen")
        z2_relay = self.sql_fetch("relay", "kitchen")
        z2_active = self.sql_fetch("active", "kitchen")
        ##Upstairs Update
        z3_set = self.sql_fetch("settemp", "upstairs")
        z3_temp = self.sql_fetch("temp", "upstairs")
        z3_relay = self.sql_fetch("relay", "upstairs")
        z3_active = self.sql_fetch("active", "upstairs")
        ##Control
        z4_active = self.sql_fetch("active", "control")
        z4_hold = self.sql_fetch("hold", "control")
        
        self.living_temp.set (str("Living:\nSet: " + str(z1_set) + "\nTemp:\n" + str(z1_temp) +self.degree_sign))
        self.kitchen_temp.set (str("Kitchen:\nSet: " + str(z2_set) + "\nTemp:\n" + str(z2_temp) +self.degree_sign))
        self.upstairs_temp.set (str("Upstairs:\nSet: " + str(z3_set) + "\nTemp:\n" + str(z3_temp) +self.degree_sign))
        if z1_relay == 1:
            self.living_label.configure(fg="green")
        elif z1_relay == 0:
            if(z1_motion == 1):
                self.living_label.configure(fg="white")
            elif(z1_motion == 0):
                self.living_label.configure(fg="yellow")
        
        if z2_relay == 1:
            self.kitchen_label.configure(fg="green")
        elif z2_relay == 0:
            self.kitchen_label.configure(fg="white")
            
        if z3_relay == 1:
            self.upstairs_label.configure(fg="green")
        elif z3_relay == 0:
            self.upstairs_label.configure(fg="white")
        
            
        if(z2_active == 0):
            self.kitchen_label.configure(fg="red")
        if(z3_active == 0):
            self.upstairs_label.configure(fg="red")
        if(z4_active == 0):
            self.control_label.configure(fg="red")
            self.control_temp.set (str("Control\nOffline"))
        if(z4_active == 1):
            self.control_label.configure(fg="white")
            self.control_temp.set (str("Control\nOnline"))
        if(z4_hold == 1):
            self.away_button.configure(bg="red")
    
        root = self.master
        self.master.after(400, self.update)
        
        
class Settings():
    def __init__(self, master):
       self.master = tk.Tk()
       self.master.attributes("-fullscreen", True)
       #self.master.geometry("100x100")
       self.screen_width = self.master.winfo_screenwidth()
       self.screen_height = self.master.winfo_screenheight()

       
       ## tkinter methods for setting up GUI
       self.layout_set() 
       self.panel_header()
       ##Continuiously running methods for updates
          
    def layout_set(self):
        ##Main Frames
        self.Header = tk.Frame(self.master, height=(self.screen_height * .25), width=self.screen_width, bg="black")
        self.Center = tk.Frame(self.master, height=(self.screen_height * .5), width=self.screen_width, bg="black")
        self.Footer = tk.Frame(self.master, height=(self.screen_height * .25), width=self.screen_width, bg="black")

        ##Sub Frames
        #Header
        self.Zone = tk.Frame(self.Header, height=(self.screen_height * .25), width=(self.screen_width * .25), bg="black")
        self.Time = tk.Frame(self.Header, height=(self.screen_height * .25), width=(self.screen_width * .5), bg="black")
        self.Exit = tk.Frame(self.Header, height=(self.screen_height * .25), width=(self.screen_width * .25), bg="black")
        #Center
        self.Info = tk.Frame(self.Center, height=(self.screen_height * .5), width=(self.screen_width * .2), bg="black")
        self.Status = tk.Frame(self.Center, height=(self.screen_height * .5), width=(self.screen_width * .6), bg="black")
        self.Mode = tk.Frame(self.Center, height=(self.screen_height * .5), width=(self.screen_width * .2), bg="black")

        ## Place Frames
        #Main Frames
        self.Header.grid(column=0, row=0)
        self.Center.grid(column=0, row=1)
        self.Footer.grid(column=0, row=2, sticky='nsew')
        #Header Frames
        self.Zone.grid(column=0, row=0)
        self.Time.grid(column=1, row=0)
        self.Exit.grid(column=2, row=0)
        #self.Time.grid_columnconfigure(0, minsize=(self.screen_width * .5))
        #elf.Zone.grid_columnconfigure(0, minsize=(self.screen_width * .25))
        #self.Exit.grid_columnconfigure(0, minsize=(self.screen_width * .25))
        
        #Center Frames
        #self.Status.grid_columnconfigure(0, minsize=(self.screen_width * .3))
        #self.Status.grid_columnconfigure(1, minsize=(self.screen_width * .3))
        #self.Mode.grid_columnconfigure(0, minsize=(self.screen_width * .2))
        #self.Info.grid_columnconfigure(0, weight=1, minsize=(self.screen_width * .2))
        self.Info.grid(column=0, row=0)
        self.Status.grid(column=1, row=0)
        self.Mode.grid(column=2, row=0)
        
        ##Footer
        
        self.Footer.grid_rowconfigure(0, weight=1)
    def panel_header(self):
        #### Header Panel #####
        
        ## Zone Panel
        #Selected Zone
        #Date/Time
        
        self.time_current= tk.StringVar()
        self.time_string = time.strftime('%A \n%-I:%M %p')
        self.time_current.set(str(self.time_string))
        self.time_current_label= tk.Label(self.Time,  textvariable=self.time_current, font=("Helvetica 40"), bg = "black", fg="white").grid(column=0, row=0)
        
        ##Exit Panel
        #Exit Button
        exit_button_txt = tk.StringVar()
        exit_button_txt.set(str("Exit"))
        exit_button = tk.Button(self.Exit, font="Verdana 40", highlightthickness=0, borderwidth=0, textvariable=exit_button_txt, command=self.exit, bg="black", fg="red", activebackground="black", activeforeground="red")
        exit_button.grid(column=0, row=0, sticky="nsew")

    
    def exit(self):
        ##Exit GUI
        self.master.destroy()     
        





        
root = tk.Tk()
app = GUI(root)
root.mainloop()