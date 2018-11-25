import pymysql.cursors
import MySQLdb
global c
##conn = pymysql.connect(host='localhost',
##                             user='pi',
##                             password='python',
##                             db='thermostat',
##                             charset='utf8mb4',
##                             cursorclass=pymysql.cursors.DictCursor)
##c = conn.cursor()
##conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
##c = conn.cursor (MySQLdb.cursors.DictCursor)
##
##do_this = 1
##zone = 'living'
##sql = ("UPDATE settings set relay = '1' WHERE zone = 'living'""")
##val = (do_this, zone)
##c.execute(sql)
##conn.commit()

##conn = MySQLdb.connect("localhost","pi","python","thermostat", port=3306 )
##c = conn.cursor (MySQLdb.cursors.DictCursor)
##try:
##    hold = 0
##    zone = 'living'
##    sql = ("UPDATE settings SET relay = '1' WHERE zone = 'living'""")
##    val = (hold, zone)
##    c.execute(sql)
##    conn.commit()
##    do_this = 0
##    sql = ("UPDATE settings set relay = %s WHERE zone = %s""")
##    val = (do_this, zone)
##    c.execute(sql, val)
##    conn.commit()
##except:
##    print("Error updating hold")
##try:
##        #GPIO.output(pin, GPIO.LOW)
##        zone = 'living'
##        relay_State = 0
##        try:
##            sql = "UPDATE settings SET relay = '0' WHERE zone = 'living'"""
##            val = (relay_State, zone)
##            c.execute(sql)
##            conn.commit()
##        except:
##            print("Database Error in Relay Off")
##except:
##    print("Error")
zone = 'living'
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
        print("error")
        



value = float(sql_fetch('settemp', zone))
print(value)
##try:
##
##    c.execute("SELECT * FROM settings WHERE zone = 'living'")
##    row = c.fetchone()
##    
##    print(row)
##    print(row['relay'])
##    #backup_Temp = float(row[1])
##    #hold_Temp = int(row[2])
##    #last_motion = int(row[4])
##except:
##    print("error")
