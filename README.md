# Turing

## How it works:
This script will connect to your IRC server (localhost by default) and respond to various prompts:
- Typing ++ in IRC will give karma to an item (e.g. Turing++)
- Typing -- in IRC will take karma away from an item (e.g. Turing--)
- Typing !rank and then an item will let you know how much karma it has (e.g. !rank Turing)
- Typing !top will list the top 5 items by karma
- Typing !bottom will list the bottom 5 items by karma
- Typing !weather <ZIP code> will provide weather info (e.g. !weather 12345)
- Typing !astronomy will provide moon information and sunset/sunrise time
- Typing !define will lookup a word's definition (e.g. !define chat)
- Typing !$stock will provide a current quote for the stock specified (e.g. !$AMD)
- Typing !help will print a list of options

## Visual Examples:

#### Weather

![image](https://user-images.githubusercontent.com/7861962/61971596-52c25980-af94-11e9-87b3-d5205f74f557.png)

#### Astronomy

![ScreenShot](https://cloud.githubusercontent.com/assets/7861962/21195315/28ad5fce-c1e8-11e6-81b5-1e9c3c86c284.PNG)

#### Karma

![ScreenShot](https://cloud.githubusercontent.com/assets/7861962/21195292/0efb60b2-c1e8-11e6-9c9b-4c2c1248fdd2.PNG)

#### Dictionary

![ScreenShot](https://user-images.githubusercontent.com/7861962/39677455-e20c261c-512f-11e8-96e8-9051a44c1cdd.png)

#### Stock Quotes

![ScreenShot](https://cloud.githubusercontent.com/assets/7861962/23950769/1fab8d2e-095a-11e7-8d76-0e661770e3e6.PNG)

#### Periodic Earthquake Check (see notes)

![ScreenShot](https://cloud.githubusercontent.com/assets/7861962/21195168/8c04aed4-c1e7-11e6-85a8-8534b9d5162e.PNG)

#### Periodic Strava Activity Check (see notes)

![ScreenShot](https://cloud.githubusercontent.com/assets/7861962/22960593/cbeeb7c8-f2f3-11e6-8514-bc5ee76c8ebe.PNG)

## Notes:

- Turing will check every couple minutes for earthquakes around the world and report them in IRC.
- Turing will check your Strava feed every couple minutes for new activities and report them in IRC.
- Turing uses json load/dump to periodically store existing karma in a file and load it on startup.
- Turing calls parameters from a config file called turing.cfg (typically dropped in /opt/turing with the script)

### [The script is named after Alan Turing]
