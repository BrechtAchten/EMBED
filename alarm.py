'''
import schedule
import time
import subprocess

def alarm():
    subprocess.call('')

alarm_time = '7:00'
schedule.every().day.at(alarm_time).do(alarm)

while True:
    schedule.run_pending()
    time.sleep(1)
'''
# code modified, tweaked and tailored from code by bertwert 
# on RPi forum thread topic 91796
import RPi.GPIO as GPIO
import subprocess
import time
import schedule
import datetime
import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from multiprocessing import Process
import os.path
import threading
from datetime import datetime
import time
import pygame

SCOPES = ['https://www.googleapis.com/auth/calender.readonly']


class alarmThread (threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.name = "Alarm thread"
		GPIO.setmode(GPIO.BCM)
		GPIO.setwarnings(False)
		GPIO.setup(21, GPIO.IN)
		pygame.mixer.init()
	def run(self):
		isPlaying = True
		pygame.mixer.music.load("/home/pi/Documents/Emsys_project/alarm.wav")
		pygame.mixer.music.play()
		startTime = datetime.now()
		while(isPlaying):
			print(GPIO.input(21))
			isPlaying = GPIO.input(21) and pygame.mixer.music.get_busy() and ((startTime - datetime.now()).total_seconds() < 10)
			time.sleep(0.1)
		pygame.mixer.music.stop()

def alarm():
    	alarm = alarmThread()
		alarm.start()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
 
# GPIO ports for the 7seg pin
segments =  (4,17,27,22,5,6,13)
 
for segment in segments:
    GPIO.setup(segment, GPIO.OUT)
    #active high
    GPIO.output(segment, 0)
    
# GPIO ports for the decimal point(s)
dps = (19,)

for dp in dps:
    GPIO.setup(dp, GPIO.OUT)
    #active high
    GPIO.output(dp, 0)
 
# GPIO ports for the digit 0-3 pins 
digits = (18,23,24,25)
 
for digit in digits:
    GPIO.setup(digit, GPIO.OUT)
    #active low
    GPIO.output(digit, 1)
 
num = {' ':(0,0,0,0,0,0,0),
    '0':(1,1,1,1,1,1,0),
    '1':(0,1,1,0,0,0,0),
    '2':(1,1,0,1,1,0,1),
    '3':(1,1,1,1,0,0,1),
    '4':(0,1,1,0,0,1,1),
    '5':(1,0,1,1,0,1,1),
    '6':(1,0,1,1,1,1,1),
    '7':(1,1,1,0,0,0,0),
    '8':(1,1,1,1,1,1,1),
    '9':(1,1,1,1,0,1,1)}



try:
    while True:
        schedule.run_pending()
        n = time.ctime()[11:13]+time.ctime()[14:16]
        midnightCheck = n+time.ctime()[17:19]
        s = str(n).rjust(4)
        for digit in range(4):
            for loop in range(0,7):
                GPIO.output(segments[loop], num[s[digit]][loop])
                if (int(time.ctime()[18:19])%2 == 0) and (digit == 1):
                    GPIO.output(19, 1)
                else:
                    GPIO.output(19, 0)
            GPIO.output(digits[digit], 0)
            time.sleep(0.001)
            GPIO.output(digits[digit], 1)
        
        if(midnightCheck == '000000'): #000000 zodat er op middernacht gekeken wordt naar de eerst volgende afspraak
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
            service = build('calendar', 'v3', credentials = creds)
            
            timeMin = datetime.datetime.utcnow().isoformat() + 'Z'
            timeMax = (datetime.datetime.utcnow() + datetime.timedelta(hours = 8)).isoformat() + 'Z' #sowieso om 8u opstaan
            print('Getting the upcoming event')
            events_result = service.events().list(calendarId = 'primary', timeMin = timeMin, timeMax = timeMax, maxResults = 1, orderBy = 'startTime', singleEvents = True).execute()
            events = events_result.get('items', [])
            
            if not events:
                alarm_hour = '08'
                alarm_minute = '00'
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                alarm_hour = str(int(start[11:13]) - 1)
                alarm_minute = start[14:16]
                schedule.every().day
            alarm_time = alarm_hour + ':' + alarm_minute
            print('alarm minute and hour', alarm_time)
            schedule.every().day.at(alarm_time).do(alarm)
            
finally:
    GPIO.cleanup()
