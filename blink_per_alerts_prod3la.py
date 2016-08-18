#!/usr/bin/python
# 20160428 - initial version
# 20160816 - improvements

###################
# libraries
###################

import requests
import json
import time
import urllib
import RPi.GPIO as GPIO
execfile("lm_auth_credentials.py")
GPIO.setmode(GPIO.BCM)



###################
# define vars
###################

debug      = 1
account    = "prod3la"

lm_rpc_url = 'https://' + account + '.logicmonitor.com/santaba/rpc/getAlerts?c=' + account + '&u=' + user + '&p=' + password
sleep      = 30


###################
# stop editing
###################


# init list with pin numbers

pinList = [3, 4, 17]

# loop through pins and set mode and state to 'HIGH'

for i in pinList:
  GPIO.setup(i, GPIO.OUT)

###################
# placeholder for RESTful API
###################
# base url - https://ACCOUNTNAME.logicmonitor.com/santaba/rest
# curl -v --user 'apiUser:example' -H "Content-Type: application/json" -d '{"name":"newServiceGroup","description":"testSites","disableAlerting":false'}' -X PUT "https://api.logicmonitor.com/santaba/rest/service/groups/7"
# wget --auth-no-challenge  --http-user='apiUser' --http-password='example' "https://api.logicmonitor.com/santaba/rest/service/groups"
# Authorization:Basic `echo -n username:password | base64`


###################
# rpc api
###################

lm_alert_filter = {
  'id': '',
  'type': '',
  'group': '',
  'host': '',
  'hostId': '',
  'dataSource': '',
  'dataSourceName': '',
  'dataPoint': '',
  'startEpoch': '',
  'endEpoch': '',
  'endTime': '',
  'ackFilter': '',
  'filterSDT': '',
  'level': '',
  'orderBy': '',
  'orderDirection': '',
  'includeInactive': '',
  'needTotal': '',
  'results': '',
  'start': '',
  'needMessage': ''
  }

def turn_leds_off(off_time=0):
  for i in pinList:
    GPIO.output(i, GPIO.HIGH)
  time.sleep(off_time);

# functions
def blink_led(color,count,seconds):
  "this blinks an LED"
  while (count > 0):
     turn_leds_off(.08)
     if color == "green" : pin = 3
     if color == "yellow": pin = 4
     if color == "red"   : pin = 17

     GPIO.output(pin, GPIO.LOW)
     time.sleep(seconds);
     GPIO.output(pin, GPIO.HIGH)
     count -= 1
  return

def solid_led(color):
  "this turns the green LED on"
  turn_leds_off(0)
  if color == "green" : pin = 3
  if color == "yellow": pin = 4
  if color == "red"   : pin = 17
  GPIO.output(pin, GPIO.LOW)
  return


def fetch_alerts(lm_rpc_url,lm_alert_filter):
  ## fetch alerts
  alerts = requests.get(lm_rpc_url,params=lm_alert_filter)

  ## print the url for debugging purposes
  #if debug: print lm_rpc_url

  ## pretty print the output
  #if debug: print json.dumps(alerts.json(), sort_keys=True,indent=4, separators=(',', ': '))

  ## parse json into native python object/array
  ## datastructure looks like parsed_alerts['data']['alerts'][INDEX]['key']
  parsed_alerts = json.loads(alerts.content)
  return parsed_alerts

##
## cycle_tower()
##
def cycle_tower():
  "startup sequence for the tower"
  turn_leds_off()
  blink_led("green",1,1)
  blink_led("yellow",1,1)
  blink_led("red",1,1)
  solid_led("green")
  return

def blink_per_alert(alerts):
  ## loop through array and count alerts
  count_warn     = 0
  count_error    = 0
  count_critical = 0
  for alert in alerts['data']['alerts']:
    if debug: print "host: " + alert['host'] + " | datasource : " + alert['dataSource'] + " | level: " + alert['level']
    if alert['level'] == "warn":
      count_warn     +=1
    if alert['level'] == "error":
      count_error    +=1
    if alert['level'] == "critical":
      count_critical +=1

  ## print alerts
  for alert in alerts['data']['alerts']:
    if debug: print "host: " + alert['host'] + " | datasource : " + alert['dataSource'] + " | level: " + alert['level']

  ## more debugging output
  if debug: print "warning alert count : " + str(count_warn)
  if debug: print "error alert count   : " + str(count_error)
  if debug: print "critical alert count: " + str(count_critical)

  count_total = count_warn + count_error + count_critical

  ## now blink LED
  if count_warn > 0:
      #blink_led("yellow",count_warn,1)
      blink_led("yellow",count_warn,count_total/count_warn)
      solid_led("yellow")
  if count_error > 0:
      #blink_led("red",count_error,1)
      blink_led("red",count_error,count_total/count_warn)
      solid_led("red")
  if count_critical > 0:
      #blink_led("red",count_critical,1)
      blink_led("red",count_critical,count_total/count_warn)
      solid_led("red")

  if ( count_warn == 0 ) and ( count_error == 0 ) and (count_critical == 0 ):
      solid_led("green")

  return alert['level']


# main control
cycle_tower()

while True:
  try:
    parsed_alerts = fetch_alerts(lm_rpc_url,lm_alert_filter)
    blink_per_alert(parsed_alerts)
    print "looping..."
    time.sleep(sleep);
  except (KeyboardInterrupt, SystemExit):

    ## confirmation we're done
    print "cleaning up..."
    GPIO.cleanup()
    break

if debug: print "\nall done!"
