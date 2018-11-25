####################
## Functions
####################

def relay_On(pin):
    global relay_State
    global zone
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    try:
        GPIO.output(pin, GPIO.HIGH)
        relay_State = 1
        try:
            sql = """UPDATE settings SET relay = %s WHERE zone = %s"""
            val = (relay_State, zone)
            c.execute(sql, val)
            conn.commit()
        except:
            print("Database Error in Relay ON")
    except:
        print("Error Starting Relay")
        relay_State = 0
    


def relay_Off(pin):
    global relay_State
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin, GPIO.OUT) ## Relay SETUP
    GPIO.setwarnings(False)
    conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
    c = conn.cursor (MySQLdb.cursors.DictCursor)
    try:
        GPIO.output(pin, GPIO.LOW)
        relay_State = 0
        try:
            sql = """UPDATE settings SET relay = %s WHERE zone = %s"""
            val = (relay_State, zone)
            c.execute(sql, val)
            conn.commit()
        except:
            print("Database Error in Relay ON")
            
    except:
        print("Error Stopping Relay")
        relay_State = 1
        

def send_Notification(title, body):
   
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
      urllib.parse.urlencode({
            "token": "awmq2qh4qoijvztozwuvte5qdbikhm",
            "user": "u9yffbyi7ppxhcw79xwfwg5afhszk2",
            "message": body,
        }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()
def log(message):
    now = datetime.now()
    string_Time = now.strftime('%b-%d-%I:%M:%S')
    log_Info = str("\n" + string_Time + " - " + str(message))
    print(log_Info)
def screen_print():
    global relay_State
    global set_Temp
    now = datetime.now()
    string_Time = now.strftime('%b-%d-%I:%M:%S')
    if (relay_State == 1):
            string_Info = str("\n" + string_Time + " - Relay ON  - " + "Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
            
    elif (relay_State == 0):

            string_Info = str("\n" + string_Time + " - Relay OFF - " + "Current Temp is: " + str(new_Temperature) + " F"+ "  Humidity is: " + str(new_Humidity) + " Thermostat is set at: " + str(set_Temp))
    return string_Info

    print(string_Info)

