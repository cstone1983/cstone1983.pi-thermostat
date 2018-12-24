import os, subprocess, time
os.environ['DISPLAY'] = ":0"

displayison = False
maxidle = 2*60 # seconds
lastsignaled = 0
##while True:
##    now = time.time()
##    if GPIO.input(PIR):
##        if not displayison:
##            subprocess.call('xset dpms force on', shell=True)
##            displayison = True
##        lastsignaled = now
##    else:
##        if now-lastsignaled > maxidle:
##            if displayison:
##                subprocess.call('xset dpms force off', shell=True)
##                displayison = False
##    time.sleep(1)
subprocess.call('xset dpms force off', shell=True)
time.sleep(5)
subprocess.call('xset dpms force on', shell=True)

