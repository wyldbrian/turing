#!/bin/python

# +-----------------------------------------------------------------------+
# | File Name: turing_bot.py                                              |
# +-----------------------------------------------------------------------+
# | Description: Turing watches an IRC channel and responds to prompts    |
# +-----------------------------------------------------------------------+
# | Usage: Use ++ or -- to hand out or take away karma (e.g. wyldbrian++) |
# |        Use !rank to check an items karma rank (e.g. !rank wyldbrian)  |
# |        Use !top to see the top 5 items by karma                       |
# |        Use !bottom to see the bottom 5 items by karma                 |
# |        Use !weather City,State to check weather                       |
# |        Use !astronomy to check moon info and sunset/sunrise times     |
# |        Use !$stock to check current quote for a stock (e.g. !$AMD)    |
# +-----------------------------------------------------------------------+
# | Authors: wyldbrian                                                    |
# +-----------------------------------------------------------------------+
# | Date: 2017-12-28                                                      |
# +-----------------------------------------------------------------------+
# | Version: 1.5.7                                                        |
# +-----------------------------------------------------------------------+

####################################################
#             Import necessary modules             #
####################################################

import re
import ssl
import sys
import json
import socket
import urllib2
import logging
import threading
from time import sleep
from datetime import datetime, time
from ConfigParser import ConfigParser

####################################################
#                Setup config parser               #
####################################################

config = ConfigParser()
config.read('turing.cfg')

####################################################
#              Set logging parameters              #
####################################################

try:
    logfile = config.get('IRC', 'log')
except BaseException:
    logfile = '/var/log/turing.log'

loglevel = logging.INFO
logformat = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(filename=logfile, format=logformat, level=loglevel)

####################################################
#             Set IRC connection values            #
####################################################

try:
    tls = config.getboolean('IRC', 'tls')
    port = config.getint('IRC', 'port')
    quake = config.getboolean('Features', 'quake')
    server = config.get('IRC', 'host')
    strava = config.getboolean('Features', 'strava')
    channel = config.get('IRC', 'channel')
    botnick = config.get('IRC', 'nick')
    passreq = config.getboolean('IRC', 'passreq')
    mag_thresh = config.getint('Earthquake', 'mag_thresh')
    weather_key = config.get('API Keys', 'weather_key')
    if strava:
        strava_key = config.get('API Keys', 'strava_key')
    if passreq:
        password = config.get('IRC', 'password')
except BaseException:
    message = "Exiting: unable to get config values"
    logging.critical(message)
    sys.exit()

####################################################
#          Create karma save/load process          #
####################################################

karma_val = []
karma_num = []


def karmaload():
    global karma_val
    global karma_num
    load_val = open("karma_val.json")
    load_num = open("karma_num.json")
    karma_val = json.loads(load_val.read())
    karma_num = json.loads(load_num.read())
    load_val.close()
    load_num.close()


def karmasave():
    threading.Timer(30, karmasave).start()
    global karma_val
    global karma_num
    save_val = file("karma_val.json", "w")
    save_num = file("karma_num.json", "w")
    save_val.write(json.dumps(karma_val))
    save_num.write(json.dumps(karma_num))
    save_val.close()
    save_num.close()


try:
    karmaload()
except BaseException:
    logging.critical('Karmaload failed, exiting')
    sys.exit()
else:
    karmasave()

####################################################
#        Create earthquake save/load process       #
####################################################

quake_id = []


def quakeload():
    global quake_id
    load_quakes = open("quake_id.json")
    quake_id = json.loads(load_quakes.read())
    load_quakes.close()


def quakesave():
    threading.Timer(30, quakesave).start()
    global quake_id
    save_quakes = file("quake_id.json", "w")
    save_quakes.write(json.dumps(quake_id))
    save_quakes.close()


try:
    quakeload()
except BaseException:
    logging.critical('Quakeload failed, exiting')
    sys.exit()
else:
    quakesave()

####################################################
#          Create strava save/load process         #
####################################################

strava_id = []


def stravaload():
    global strava_id
    load_strava = open("strava_id.json")
    strava_id = json.loads(load_strava.read())
    load_strava.close()


def stravasave():
    threading.Timer(30, stravasave).start()
    global strava_id
    save_strava = file("strava_id.json", "w")
    save_strava.write(json.dumps(strava_id))
    save_strava.close()


try:
    stravaload()
except BaseException:
    logging.critical('Stravaload failed, exiting')
    sys.exit()
else:
    stravasave()

####################################################
#          Build karma functions for IRC           #
####################################################


def karmaup():
    try:
        karma_up = (text.split("++")[0]).split(":")[2].rsplit(None, 1)[-1].lower()
    except IndexError:
        message = "What would you like to give Karma to? (e.g. Karmabot++)"
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
        return
    if karma_up in karma_val:
        idx = karma_val.index(karma_up)
        num = karma_num[idx]
        karma_num[idx] = int(num) + 1
        user = (text.split(":")[1]).split("!")[0]
        logmsg = user + " gave karma to " + karma_up + " (++)"
        logging.info(logmsg)
    elif karma_up not in karma_val:
        karma_val.append(karma_up)
        karma_num.append(1)
        user = (text.split(":")[1]).split("!")[0]
        logmsg = user + " gave karma to " + karma_up + " (++)"
        logging.info(logmsg)


def karmadown():
    try:
        karma_down = (text.split("--")[0]).split(":")[2].rsplit(None, 1)[-1].lower()
    except IndexError:
        message = "What would you like to take Karma away from? (e.g. Karmabot--)"
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
        return
    if karma_down in karma_val:
        idx = karma_val.index(karma_down)
        num = karma_num[idx]
        karma_num[idx] = int(num) - 1
        user = (text.split(":")[1]).split("!")[0]
        logmsg = user + " took karma away from " + karma_down + " (--)"
        logging.info(logmsg)
    elif karma_down not in karma_val:
        karma_val.append(karma_down)
        karma_num.append(-1)
        user = (text.split(":")[1]).split("!")[0]
        logmsg = user + " took karma away from " + karma_down + " (--)"
        logging.info(logmsg)


def karmarank():
    try:
        rank = (text.split(':!rank')[1]).strip().lower()
    except IndexError:
        message = "What would you like to check the rank of? (e.g. !rank Karmabot)"
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
        return
    if rank in karma_val:
        idx = karma_val.index(rank)
        num = karma_num[idx]
        message = (rank + " has " + str(num) + " points of karma!")
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
    elif rank not in karma_val:
        message = (rank + " doesn't have any karma yet!")
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')


def topkarma():
    top_results = sorted(zip(karma_num, karma_val), reverse=True)[:5]
    irc.send('PRIVMSG ' + channel + ' :' + "## TOP 5 KARMA RECIPIENTS ##" + '\r\n')
    for (x, y) in top_results:
        message = (y + ": " + str(x))
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')


def bottomkarma():
    top_results = sorted(zip(karma_num, karma_val), reverse=False)[:5]
    irc.send('PRIVMSG ' + channel + ' :' + "## BOTTOM 5 KARMA RECIPIENTS ##" + '\r\n')
    for (x, y) in top_results:
        message = (y + ": " + str(x))
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')

####################################################
#          Build weather function for IRC          #
####################################################


def weathercheck():
    try:
        city = (text.split("!weather")[1]).split(",")[0].lstrip().replace(" ", "_")
        state = (text.split("!weather")[1]).split(",")[1].strip().replace(" ", "_")
    except IndexError:
        message = "What city's weather would you like to check? (e.g. !weather Bend,OR)"
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
        return
    try:
        weather_call = urllib2.urlopen('http://api.wunderground.com/api/%s/geolookup/conditions/q/%s/%s.json' % (weather_key, state, city), timeout=2)
    except (socket.timeout, urllib2.URLError):
        message = "Weather API timed out, please try again in a few seconds."
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
        logging.warning(message)
        return
    weather_output = weather_call.read()
    weather_call.close()
    weather_dict = json.loads(weather_output)
    try:
        temp = weather_dict['current_observation']['temperature_string']
        location = weather_dict['location']['city']
        condition = weather_dict['current_observation']['weather']
    except KeyError:
        if "keynotfound" in weather_output or "missingkey" in weather_output:
            message = ("Weather API rate limit reached, please try again in a few seconds.")
            irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
            logging.warning(message)
            return
        elif "querynotfound" in weather_output or "conditions" in weather_output:
            message = ("No weather results found for %s,%s" % (city.replace("_", " "), state.replace("_", " ")))
            irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
            logging.warning(message)
            return
        else:
            message = ("Unknown API error occured, please try again later")
            irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
            logging.warning(message)
            return
    message = "The weather in %s is currently showing %s with a temperature of %s" % (location, condition, temp)
    irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')

####################################################
#        Build function for astronomy checks       #
####################################################


def astronomycheck():
    try:
        astronomy_call = urllib2.urlopen('http://api.wunderground.com/api/%s//astronomy/q/OR/Bend.json' % (weather_key), timeout=2)
    except (socket.timeout, urllib2.URLError):
        message = "Caught timeout/url exception when hitting Weather Underground API"
        logging.critical(message)
        return
    astronomy_output = astronomy_call.read()
    astronomy_call.close
    astronomy_dict = json.loads(astronomy_output)
    try:
        age = astronomy_dict['moon_phase']['ageOfMoon']
        phase = astronomy_dict['moon_phase']['phaseofMoon']
        illum = astronomy_dict['moon_phase']['percentIlluminated']
        sunrise = str(astronomy_dict['moon_phase']['sunrise']['hour']) + ":" + str(astronomy_dict['moon_phase']['sunrise']['minute'])
        sunset = str(astronomy_dict['moon_phase']['sunset']['hour']) + ":" + str(astronomy_dict['moon_phase']['sunset']['minute'])
    except KeyError:
        if "keynotfound" in astronomy_output or "missingkey" in astronomy_output:
            message = ("Weather API rate limit reached, please try again in a few seconds.")
            irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
            logging.warning(message)
            return
        else:
            message = ("Unknown API error occured, please try again later")
            irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
            logging.warning(message)
            return
    first_message = "Today the moon is %s days old, %s illuminated, and in its %s phase." % (age, illum + "%", phase)
    second_message = "Today the sun rises at %s and sets at %s." % (sunrise, sunset)
    irc.send('PRIVMSG ' + channel + ' :' + first_message + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + second_message + '\r\n')

####################################################
#       Build function for earthquake checks       #
####################################################


def quakecheck():
    threading.Timer(120, quakecheck).start()
    try:
        quake_call = urllib2.urlopen('http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson', timeout=5)
    except (socket.timeout, urllib2.URLError):
        message = "Caught timeout/url exception when contacting USGS API"
        logging.critical(message)
        return
    quake_output = quake_call.read()
    quake_call.close
    quake_dict = json.loads(quake_output)
    global quake_id
    for quake in quake_dict['features']:
        if quake['id'] not in quake_id:
            quake_id.append(quake['id'])
            mag = quake['properties']['mag']
            location = quake['properties']['place']
            message = "%s magnitude earthquake detected %s" % (mag, location)
            try:
                if int(mag) >= mag_thresh:
                    irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
                    logging.warning(message)
            except BaseException:
                message = "Caught exception trying to post quake info to IRC"
                logging.critical(message)
                return

####################################################
#         Build function for strava checks         #
####################################################


def stravacheck():
    threading.Timer(120, stravacheck).start()
    try:
        req = urllib2.Request('https://www.strava.com/api/v3/activities/following')
        req.add_header('Authorization', 'Bearer %s' % (strava_key))
        strava_call = urllib2.urlopen(req)
    except (socket.timeout, urllib2.URLError):
        message = "Caught timeout/url exception when contacting Strava API"
        logging.critical(message)
        return
    strava_output = strava_call.read()
    strava_call.close
    strava_dict = json.loads(strava_output)
    global strava_id
    for activity in strava_dict:
        if activity['id'] not in strava_id:
            strava_id.append(activity['id'])
            first = activity['athlete']['firstname']
            last = activity['athlete']['lastname']
            type = activity['type']
            name = activity['name']
            miles = round((activity['distance'] / 1609.344), 1)
            message = "%s %s just completed a %s mile %s - %s" % (first, last, miles, type, name)
            try:
                irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
            except BaseException:
                message = "Caught exception trying to post strava info to IRC"
                logging.critical(message)
                return
            logging.info(message)

####################################################
#         Build functions for stock checks         #
####################################################


def marketopen():
    day = datetime.today().weekday()
    now = datetime.utcnow().time()
    if day < 5 and now >= time(14, 30) and now <= time(21, 00):
        return True
    else:
        return False


def stockcheck():
    try:
        stock = text.split(':!$')[1].rstrip()
    except IndexError:
        message = "\x0304Please use correct format (e.g. !$AMD)\x03"
        irc.send('PRIVMSG ' + channel + ' :' + message + '\r\n')
        return
    try:
        url = 'http://finance.google.com/finance?q='
        content = urllib2.urlopen(url + stock).read()
        name = re.search("_companyName.=.*?['](.*?)[']", content).group(1)
        ticker = re.search("_ticker.=.*?['](.*?)[']", content).group(1)
        if marketopen():
            price = re.search('id="ref_(.+)_l".*?>(.*?)<', content).group(2)
            change = re.search('id="ref_(.+)_c".*?>(.*?)<', content).group(2)
            percent = re.search('id="ref_(.+)_cp".*?>(.*?)<', content).group(2)
            status = "\x0303Market Open\x03"
        else:
            try:
                price = re.search('id="ref_(.+)_el".*?>(.*?)<', content).group(2)
                change = re.search('id="ref_(.+)_ec".*?>(.*?)<', content).group(2)
                percent = re.search('id="ref_(.+)_ecp".*?>(.*?)<', content).group(2)
                status = "\x0304Market Closed\x03"
            except AttributeError:
                price = re.search('id="ref_(.+)_l".*?>(.*?)<', content).group(2)
                change = re.search('id="ref_(.+)_c".*?>(.*?)<', content).group(2)
                percent = re.search('id="ref_(.+)_cp".*?>(.*?)<', content).group(2)
                status = "\x0304Market Closed\x03"
        if "+" in change:
            message = "%s | %s | %s | \x0303$%s\x03 | \x0303%s %s\x03" % (ticker, name, status, price, change, percent)
        else:
            message = "%s | %s | %s | \x0304$%s\x03 | \x0304%s %s\x03" % (ticker, name, status, price, change, percent)
    except socket.timeout:
        message = "\x0304Timeout occurred, please try again in a few seconds.\x03"
    except AttributeError:
        message = "\x0304No quote found, try the full ticker (e.g. !$NYSE:%s)\x03" % (stock.upper())
    except urllib2.URLError:
        message = "\x0304Please use the correct format (e.g. !$AMD)\x03"
    except BaseException:
        message = "\x0304Unknown error occured, please try again later\x03"
    irc.send('PRIVMSG ' + channel + ' :' + message.replace("\\x26", "&") + '\r\n')

####################################################
#              Build IRC help function             #
####################################################


def help():
    irc.send('PRIVMSG ' + channel + ' :' + "     ##############################TURING USAGE##############################" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !weather = check weather for a specific location (e.g. !weather Bend,OR)" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     ++ or -- = give or take karma from whatever you want (e.g. Turing++)" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !rank = show the rank of a particular thing (e.g. !rank Turing)" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !astronomy = check moon information and sunset/sunrise times" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !top or !bottom = show the top or bottom 5 items by Karma" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !$stock = show the current quote for a stock (e.g. !$AMD)" + '\r\n')

####################################################
#            Build IRC connect function            #
####################################################


def connect():
    global irc
    if tls:
        irc = ssl.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    else:
        irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    while True:
        try:
            irc.connect((server, port))
        except socket.error:
            sleep(30)
            continue
        break
    if passreq:
        irc.send("PASS " + password + "\n")
        irc.send("NICK " + botnick + "\n")
        irc.send("USER " + botnick + " " + botnick + " " + botnick + " :Machines take me by surprise with great frequency.\n")
        irc.send("JOIN " + channel + "\n")
    else:
        irc.send("USER " + botnick + " " + botnick + " " + botnick + " :Machines take me by surprise with great frequency.\n")
        irc.send("NICK " + botnick + "\n")
        irc.send("JOIN " + channel + "\n")

####################################################
# Watch IRC chat for key values and run functions  #
####################################################


connect()

if quake:
    try:
        quakecheck()
    except BaseException:
        message = "Unable to start quakecheck, starting Turing without it"
        logging.critical(message)
        pass

if strava:
    try:
        stravacheck()
    except BaseException:
        message = "Unable to start stravacheck, starting Turing without it"
        logging.critical(message)
        pass

while True:
    text = irc.recv(1024)
    if text.find('PING') != -1:
        irc.send('PONG ' + text.split()[1] + '\r\n')
    elif text.find('++') != -1 and text.find(channel) != -1:
        karmaup()
    elif text.find('--') != -1 and text.find(channel) != -1:
        karmadown()
    elif text.find('!rank') != -1 and text.find(channel) != -1:
        karmarank()
    elif text.find('!top') != -1 and text.find(channel) != -1:
        topkarma()
    elif text.find('!bottom') != -1 and text.find(channel) != -1:
        bottomkarma()
    elif text.find('!weather') != -1 and text.find(channel) != -1:
        weathercheck()
    elif text.find('!astronomy') != -1 and text.find(channel) != -1:
        astronomycheck()
    elif text.find('!$') != -1 and text.find(channel) != -1:
        stockcheck()
    elif text.find('!help') != -1 and text.find(channel) != -1:
        sleep(.5)
        help()
    elif len(text) == 0:
        while True:
            try:
                sleep(30)
                connect()
            except BaseException:
                continue
            break
