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
# | Date: 2019-07-22                                                      |
# +-----------------------------------------------------------------------+
# | Version: 1.7.4                                                        |
# +-----------------------------------------------------------------------+

####################################################
#             Import necessary modules             #
####################################################

import re
import ssl
import sys
import json
import socket
import requests
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
    oxford_id = config.get('API Keys', 'oxford_id')
    oxford_key = config.get('API Keys', 'oxford_key')
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
#           Global IRC message function            #
####################################################

def chat(msg):
    irc.send('PRIVMSG ' + channel + ' :' + msg + '\r\n')

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
    global quake_id
    save_quakes = file("quake_id.json", "w")
    save_quakes.write(json.dumps(quake_id))
    save_quakes.close()


try:
    quakeload()
except ValueError:
    logging.critical('Quakeload discovered no values, moving on.')
except BaseException:
    logging.critical('Quakeload failed, moving on.')

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
        chat(message)
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
        chat(message)
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
        chat(message)
        return
    if rank in karma_val:
        idx = karma_val.index(rank)
        num = karma_num[idx]
        message = (rank + " has " + str(num) + " points of karma!")
        chat(message)
    elif rank not in karma_val:
        message = (rank + " doesn't have any karma yet!")
        chat(message)


def topkarma():
    top_results = sorted(zip(karma_num, karma_val), reverse=True)[:5]
    irc.send('PRIVMSG ' + channel + ' :' + "## TOP 5 KARMA RECIPIENTS ##" + '\r\n')
    for (x, y) in top_results:
        message = (y + ": " + str(x))
        chat(message)


def bottomkarma():
    top_results = sorted(zip(karma_num, karma_val), reverse=False)[:5]
    irc.send('PRIVMSG ' + channel + ' :' + "## BOTTOM 5 KARMA RECIPIENTS ##" + '\r\n')
    for (x, y) in top_results:
        message = (y + ": " + str(x))
        chat(message)

####################################################
#          Build weather function for IRC          #
####################################################


def weathercheck():
    zipcode = (text.split("!weather")[1]).strip()
    try:
        url = 'https://api.openweathermap.org/data/2.5/weather?zip=%s&units=imperial&appid=%s' % (zipcode, weather_key)
        req = requests.get(url)
    except (socket.timeout, requests.RequestException):
        message = "Weather API timed out, please try again in a few seconds."
        chat(message)
        logging.warning(message)
        return
    weather_output = req.text
    weather_dict = json.loads(weather_output)
    try:
        location = weather_dict['name']
        tempf = int(weather_dict['main']['temp'])
        tempc = int((tempf - 32)*.5556)
        humidity = weather_dict['main']['humidity']
        condition = weather_dict['weather'][0]['description']
    except KeyError:
        if "requests limitation" in weather_output:
            message = ("Weather API rate limit reached, please try again in a few seconds.")
            chat(message)
            logging.warning(message)
            return
        elif "city not found" in weather_output:
            message = ("No weather results found for ZIP code %s") % zipcode
            chat(message)
            logging.warning(message)
            return
        elif "Nothing to geocode" in weather_output:
            message = "What ZIP code (US only) would you like to check the weather of? (e.g. !weather 12345)"
            chat(message)
            return
        else:
            message = ("Unknown API error occured, please try again later")
            chat(message)
            logging.warning(message)
            return
    message = "The weather in %s is currently showing %s with a temperature of %sF (%sC) and %s%% humidity" % (location, condition, tempf, tempc, humidity)
    chat(message)

####################################################
#        Build function for astronomy checks       #
####################################################


def astronomycheck():
    try:
        url = 'http://api.wunderground.com/api/%s//astronomy/q/OR/Bend.json' % weather_key
        req = requests.get(url)
    except (socket.timeout, requests.RequestException):
        message = "Caught timeout/url exception when hitting Weather Underground API"
        logging.critical(message)
        return
    astronomy_output = req.text
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
            chat(message)
            logging.warning(message)
            return
        else:
            message = ("Unknown API error occured, please try again later")
            chat(message)
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
        req = requests.get('http://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson')
    except (socket.timeout, requests.RequestException):
        message = "Caught timeout/url exception when contacting USGS API"
        logging.critical(message)
        return
    quake_output = req.text
    quake_dict = json.loads(quake_output)
    global quake_id
    for quake in quake_dict['features']:
        if quake['id'] not in quake_id:
            quake_id.append(quake['id'])
            quakesave()
            mag = quake['properties']['mag']
            location = quake['properties']['place']
            message = "%s magnitude earthquake detected %s" % (mag, location)
            try:
                if int(mag) >= mag_thresh:
                    chat(message)
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
        url = 'https://www.strava.com/api/v3/activities/following'
        headers = {'Authorization': 'Bearer %s'}  % strava_key
        req  = requests.get(url, headers=headers)
    except (socket.timeout, requests.RequestException):
        message = "Caught timeout/url exception when contacting Strava API"
        logging.critical(message)
        return
    strava_output = req.text
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
                chat(message)
            except BaseException:
                message = "Caught exception trying to post strava info to IRC"
                logging.critical(message)
                return
            logging.info(message)

####################################################
#       Build function for dictionary checks       #
####################################################

def dictionarycheck():
    try:
        word = (text.split("!define")[1]).strip()
    except IndexError:
        message = "What word would you like to lookup the definition for? (e.g. !define ace)"
        chat(message)
        return
    try:
        url = 'https://od-api.oxforddictionaries.com:443/api/v2/entries/en/%s' % word
        headers = {
            'accept': 'application/json',
            'app_id': oxford_id,
            'app_key': oxford_key
        }
        req = requests.get(url, headers=headers)
    except socket.timeout:
        message = "Oxford API timed out, please try again in a few seconds."
        chat(message)
        logging.warning(message)
        return
    try:
        oxford_output = req.text.encode('ascii', 'ignore')
        oxford_dict = json.loads(oxford_output)
    except ValueError:
        message = "No results found for %s, please try a different word." % (word)
        chat(message)
        return
    try:
        type = oxford_dict['results'][0]['lexicalEntries'][0]['lexicalCategory']['id'][:1]
        definition = oxford_dict['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['definitions'][0]
    except KeyError:
        try:
            type = oxford_dict['results'][0]['lexicalEntries'][1]['lexicalCategory']['id'][:1]
            definition = oxford_dict['results'][0]['lexicalEntries'][1]['entries'][0]['senses'][0]['definitions'][0]
        except KeyError:
            message = "No results found for %s, please try a different word." % (word)
            chat(message)
            return
    except IndexError:
        message = "No results found for %s, please try a different word." % (word)
        chat(message)
        return
    message = "%s(%s) - %s" % (word.capitalize(), type.lower(), definition.capitalize())
    chat(message)

####################################################
#         Build function for stock checks          #
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
        chat(message)
        return
    try:
        url = 'https://finance.yahoo.com/quote/%s' % stock
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/70.0.3538.77 Safari/537.36'
            }
        req  = requests.get(url, headers=headers)
        content = req.text.encode("utf-8")
        ticker = stock.upper()
        name = re.findall(r'<title>(.*?)\(%s\)' % ticker, content)[0].strip()
        if marketopen():
            price = re.findall(r'data-reactid=.\d*.>([0-9,*]+\.\d\d)</span><span\sclass=.Trsdu', content)[0]
            change = re.findall(r'data-reactid=.\d\d.>([-+]\d*\.?\d*.\([-+]?.*?\(?)</span>', content)[0]
            status = "\x0303Market Open\x03"
        else:
            try:
                price = re.findall(r'data-reactid=.\d*.>([0-9,*]+\.\d*)</span><!--', content)[0]
                change = re.findall(r'data-reactid=.\d\d.>([-+]\d*\.?\d*.\([-+]?.*?\(?)</span>', content)[1]
                status = "\x0304Market Closed\x03"
            except IndexError:
                price = re.findall(r'data-reactid=.\d*.>([0-9,*]+\.\d\d)</span><span\sclass=.Trsdu', content)[0]
                change = re.findall(r'data-reactid=.\d\d.>([-+]\d*\.?\d*.\([-+]?.*?\(?)</span>', content)[0]
                status = "\x0304Market Closed\x03"
        if "+" in change:
            message = "%s | %s | %s | \x0303$%s\x03 | \x0303%s\x03" % (ticker, name, status, price, change)
        else:
            message = "%s | %s | %s | \x0304$%s\x03 | \x0304%s\x03" % (ticker, name, status, price, change)
    except socket.timeout:
        message = "\x0304Timeout occurred, please try again in a few seconds.\x03"
    except AttributeError:
        message = "\x0304No quote found, try the full ticker (e.g. !$NYSE:%s)\x03" % (stock.upper())
    except BaseException:
        message = "\x0304Unknown error occured, please try again later\x03"
    irc.send('PRIVMSG ' + channel + ' :' + message.replace("\\x26", "&").replace("&amp;", "&") + '\r\n')

####################################################
#              Build IRC help function             #
####################################################


def help():
    irc.send('PRIVMSG ' + channel + ' :' + "     ##############################TURING USAGE##############################" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !weather = check weather for a specific ZIP code (e.g. !weather 12345)" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     ++ or -- = give or take karma from whatever you want (e.g. Turing++)" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !rank = show the rank of a particular thing (e.g. !rank Turing)" + '\r\n')
    irc.send('PRIVMSG ' + channel + ' :' + "     !define = lookup the definition of a word (e.g. !define chat)" + '\r\n')
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
        message = "Unable to start quakecheck, starting Turing without it."
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
    elif text.find('!define') != -1 and text.find(channel) != -1:
        dictionarycheck()
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
