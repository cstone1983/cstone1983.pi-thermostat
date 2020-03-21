import tkinter as tk
import time
import MySQLdb
from datetime import datetime
from tkinter import StringVar

LARGE_FONT = ("Verdana", 12)
def end():
    print("End")
class ThermostatGUI(tk.Tk):

    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        container = tk.Frame(self)
        container.grid(column=0, row=0)
        #container.grid_rowconfigure(0, weight=1)
        #container.grid_columnconfigure(0, weight=1)
        
        
        self.frames = {}
        for F in (StartPage, Settings, PageTwo):
            
            frame = F(container, self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.show_frame(StartPage)
    selected_zone = 'living'
    show_zone = ('Zone:\n'+selected_zone)
    
    
    
    ## Raise Window (show different page)
    def show_frame(self, cont):
    
        frame = self.frames[cont]
        frame.tkraise()
                   
    def end(self):
        self.destroy()

class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        controller.title("Test")
        
        controller.attributes("-fullscreen", True)
        self.screen_width = controller.winfo_screenwidth()
        self.screen_height = controller.winfo_screenheight()
        
        self.layout_set()
                
        def layout_set(self):
            ##Main Frames
            self.Header = tk.Frame(self.controller, height=(screen_height * .25), width=screen_width, bg="black")
            self.Center = tk.Frame(self.controller, height=(screen_height * .5), width=screen_width, bg="black")
            self.Footer = tk.Frame(self.controller, height=(screen_height * .25), width=screen_width, bg="black")
    
            ##Sub Frames
            #Header
            self.Zone = tk.Frame(self.Header, height=(screen_height * .25), width=(screen_width * .25), bg="black")
            self.Time = tk.Frame(self.Header, height=(screen_height * .25), width=(screen_width * .5), bg="black")
            self.Exit = tk.Frame(self.Header, height=(screen_height * .25), width=(screen_width * .25), bg="black")
            #Center
            self.Info = tk.Frame(self.Center, height=(screen_height * .5), width=(screen_width * .2), bg="black")
            self.Status = tk.Frame(self.Center, height=(screen_height * .5), width=(screen_width * .6), bg="black")
            self.Mode = tk.Frame(self.Center, height=(screen_height * .5), width=(screen_width * .2), bg="black")
    
            ## Place Frames
            #Main Frames
            self.Header.grid(column=0, row=0)
            self.Center.grid(column=0, row=1)
            self.Footer.grid(column=0, row=2)
            #Header Frames
            self.Zone.grid(column=0, row=0)
            self.Time.grid(column=1, row=0)
            self.Exit.grid(column=2, row=0)
            self.Time.grid_columnconfigure(0, minsize=(screen_width * .5))
            self.Zone.grid_columnconfigure(0, minsize=(screen_width * .25))
            self.Exit.grid_columnconfigure(0, minsize=(screen_width * .25))
            
            #Center Frames
            #self.Info.grid(column=0, row=0)
            #self.Info.grid_columnconfigure(0, weight=1, minsize=(screen_width * .2))
            #self.Status.grid(column=1, row=0)
            #self.Status.grid_columnconfigure(1, minsize=(screen_width * .6))
            #self.Mode.grid(column=2, row=0)
                    

        
        
        
        #### Header Panel #####
        ## Zone Panel
        #Selected Zone
                
        self.selected_zone = 'Living'
        self.show_zone = ('Zone:\n'+self.selected_zone)
        
        self.current_zone = StringVar()
        current_zone_label = tk.Label(self.Zone, padx=10, textvariable=self.current_zone, font=("Helvetica 24"), bg = "black", fg="white")
        self.current_zone.set (self.show_zone)
        current_zone_label.grid(column=0, row=0)

        #Date/Time
        
        self.time_current=StringVar()
        self.time_string = time.strftime('%A \n%-I:%M %p')
        self.time_current.set(str(self.time_string))
        self.time_current_label= tk.Label(self.Time,  textvariable=self.time_current, font=("Helvetica 40"), bg = "black", fg="white")
        self.time_current_label.grid(column=0, row=0)
        
        ##Exit Panel
        #Exit Button
        exit_button_txt = StringVar()
        exit_button_txt.set(str("Exit"))
        exit_button = tk.Button(self.Exit, font="Verdana 40", highlightthickness=0, borderwidth=0, textvariable=exit_button_txt,                                 command=controller.end, bg="black", fg="green", activebackground="black", activeforeground="blue")
        #exit_button.config(height=100, width=100)
        exit_button.grid(column=0, row=0, sticky="nsew")

       # u_button = tk.Button(self.Footer, text="Update", command=clock)
        #u_button.grid(column=1, row=1)
        
        self.clock()
        def select_zone(zone):
            self.selected_zone = zone
            self.show_zone = ('Zone:\n'+self.selected_zone)
            self.current_zone.set (self.show_zone)

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
        def clock(self):
            now = int(time.time())
                
            self.time_string = time.strftime('%A \n%-I:%M %p')
            time_current.config(text=str(self.time_string))
            print('clock')
            controller.after(100, self.clock) # run itself again after 1000 ms
        



class Settings(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Settings")
        label.pack(pady=10, padx=10)
        button1 = tk.Button(self, text="Start Page", command=lambda: controller.show_frame(StartPage))
        quit = tk.Button(self, text="Quit", command=end)
        button1.pack()
        quit.pack()

class PageTwo(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        self.controller = controller
        label = tk.Label(self, text="Page Two")
        label.pack(pady=10, padx=10)
        button1 = tk.Button(self, text="Start Page", command=lambda: controller.show_frame(StartPage))
        quit = tk.Button(self, text="Quit", command=end)
        button1.pack()
        quit.pack()
app = ThermostatGUI()
app.mainloop()
        