import re
import json
import discord
import requests
import traceback
from time import sleep
from datetime import datetime, time

client = discord.Client()

@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))

@client.event
async def on_message(msg):
    if msg.author == client.user:
        return

    if msg.content.startswith('!$'):
        chat = stockcheck(msg)
        await msg.channel.send(chat)
    elif msg.content.startswith('!weather'):
        chat = weathercheck(msg)
        await msg.channel.send(chat)

####################################################
#          Build weather function for IRC          #
####################################################

def weathercheck(msg):
    zipcode = msg.content.split("!weather")[1].strip()
    try:
        url = 'https://api.openweathermap.org/data/2.5/weather?zip=%s&units=imperial&appid=%s' % (zipcode, 'cc63d4ac37d6dbadd22b75b4ec8de53c')
        req = requests.get(url)
    except (requests.RequestException):
        message = "Weather API timed out, please try again in a few seconds."
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
            output = "Weather API rate limit reached, please try again in a few seconds."
            return
        elif "city not found" in weather_output:
            output = "No weather results found for ZIP code %s" % zipcode
            return
        elif "Nothing to geocode" in weather_output:
            output = "What ZIP code (US only) would you like to check the weather of? (e.g. !weather 12345)"
            return
        else:
            output = ("Unknown API error occured, please try again later")
            return
    output = "The weather in %s is currently showing %s with a temperature of %sF (%sC) and %s%% humidity" % (location, condition, tempf, tempc, humidity)
    return output

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

def stockcheck(msg):
    try:
        stock = msg.content.split('!$')[1].rstrip()
    except IndexError:
        output = "Please use correct format (e.g. !$AMD)"
        return
    try:
        url = 'https://finance.yahoo.com/quote/%s' % stock
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) \
            AppleWebKit/537.36 (KHTML, like Gecko) \
            Chrome/70.0.3538.77 Safari/537.36'
            }
        req  = requests.get(url, headers=headers)
        req_output = req.text.encode("utf-8")
        content = str(req_output)
        ticker = stock.upper()
        name = re.findall(r'<title>(.*?)\(%s\)' % ticker, content)[0].strip()
        if marketopen():
            price = re.findall(r'data-reactid=.\d*.>([0-9,*]+\.\d\d)</span><span\sclass=.Trsdu', content)[0]
            change = re.findall(r'data-reactid=.\d\d.>([-+]\d*\.?\d*.\([-+]?.*?\(?)</span>', content)[0]
            status = "Market Open"
        else:
            try:
                price = re.findall(r'data-reactid=.\d*.>([0-9,*]+\.\d*)</span><!--', content)[0]
                change = re.findall(r'data-reactid=.\d\d.>([-+]\d*\.?\d*.\([-+]?.*?\(?)</span>', content)[1]
                status = "Market Closed"
            except IndexError:
                price = re.findall(r'data-reactid=.\d*.>([0-9,*]+\.\d\d)</span><span\sclass=.Trsdu', content)[0]
                change = re.findall(r'data-reactid=.\d\d.>([-+]\d*\.?\d*.\([-+]?.*?\(?)</span>', content)[0]
                status = "Market Closed"
        if "+" in change:
            output = "%s | %s | %s | $%s | %s" % (ticker, name, status, price, change)
        else:
            output = "%s | %s | %s | $%s | %s" % (ticker, name, status, price, change)
    except AttributeError:
        output = "No quote found, try the full ticker (e.g. !$NYSE:%s)" % (stock.upper())
        traceback.print_exc()
    except BaseException:
        output = "Unknown error occured, please try again later"
        traceback.print_exc()
    return output

client.run('ODk3NTY5MjgxOTA1MTUyMDEw.YWXkiA.LQiVrx7kfB_E8NUwRv78IMp824M')