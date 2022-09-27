from adafruit_displayio_layout.layouts.grid_layout import GridLayout
from adafruit_display_text.bitmap_label import Label
import adafruit_imageload
from adafruit_magtag.magtag import MagTag
from adafruit_portalbase.network import HttpError
from displayio import Group, TileGrid
import terminalio
from rtc import RTC
import json
import time

from persistent_ram import PersistentRam
from secrets import secrets


magtag = MagTag()
# print(f'{magtag.peripherals.speaker_disable=}')  # speaker is not enabled by default
# print(f'{magtag.peripherals.neopixel_disable=}')
# print(f'{magtag.network.enabled=}')
magtag.peripherals.neopixel_disable = True # shut down to preserve power
magtag.network.enabled=False


# Screen Resolution 296 x 128
# print(f'{magtag.graphics.display.width=}')
# print(f'{magtag.graphics.display.height=}')

today_panel_width = 170 # width of the left side of the screen

ICONS_SMALL_FILE = "/bmps/weather_icons_20px.bmp"
ICONS_LARGE_FILE = "/bmps/weather_icons_70px.bmp"
ICON_MAP = ("01", "02", "03", "04", "09", "10", "11", "13", "50")

icons_small_bmp, icons_small_pal = adafruit_imageload.load(ICONS_SMALL_FILE)
icons_large_bmp, icons_large_pal = adafruit_imageload.load(ICONS_LARGE_FILE)


class HBoxLayout(Group):
    # Objects appended to the HBoxLayout are positioned after one another in the horizontal.
    # Used to position a collection of labels and TileGrid into a GridLayout in .
    # also used to concatenate text with multiple sizes
    @property
    def width(self):
        _width = 0
        for w in self:
            if isinstance(w, TileGrid):
                _width += w.width * w.tile_width
            else:
                _width += w.width * w.scale
        return _width

    @property
    def height(self):
        # this is not correct - but not really used.  TODO: fix
        return max([w.height for w in self])

    def append(self, layer):
        if not len(self):
            layer.x = 0 # the first widget starts at zero
        else:
            layer.x = self.width
        super().append(layer)

def horizontal_center(start=0, end=296, width=0):
    # returns the x value to center the object
    return ((end - start) - width)//2 + start

def display_time_day():
    # get the current time from the RTC and set the display
    hours = ['12', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']
    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    now = RTC().datetime
    hr_min = f'{hours[now.tm_hour % 12]}:{now.tm_min:02d}'
    am_pm = 'pm' if now.tm_hour > 11 else 'am'
    day = days[now.tm_wday]
    current_time = HBoxLayout()
    current_time.append(Label(terminalio.FONT, text=hr_min, color=0x000000, scale=2))
    current_time.append(Label(terminalio.FONT, text=am_pm, color=0x000000, scale=1, y=-5))
    current_time.append(Label(terminalio.FONT, text=f' {day}', color=0x000000, scale=2))
    current_time.y = 12
    current_time.x = horizontal_center(end=today_panel_width, width=current_time.width)
    magtag.splash.append(current_time)


def filter_weather_data(weather_json):
    # passed in the raw weather json (dict) from open weather maps
    # returns a dict with just the required data for the app
    # data is rounded, ready for display
    today_sd = {}
    for k in ['temp', 'humidity', 'uvi']:
        today_sd.update({k: round(weather_json['current'][k])})
    today_sd['icon'] = weather_json['current']['weather'][0]['icon']
    for k in ['min', 'max']:
        today_sd.update({k: round(weather_json['daily'][0]['temp'][k])})
    forcast_sd = []
    for i in range(1, 5):
        d = {}
        d.update({'icon': weather_json['daily'][i]['weather'][0]['icon']})
        for k in ['min', 'max']:
            d.update({k: round(weather_json['daily'][i]['temp'][k])})
        forcast_sd.append(d)
    return {'today': today_sd, 'forecast':forcast_sd}

def display_todays_weather(today):
    # passed the todays weather dictionary
    today_icon = TileGrid(icons_large_bmp, pixel_shader=icons_large_pal,
                          x=horizontal_center(end=today_panel_width, width=70),
                          y=29, width=1, height=1, tile_width=70, tile_height=70)

    # create a "FloatLayout" for the left hand side
    current_temp = HBoxLayout()
    current_temp.append(Label(terminalio.FONT, text=f'{today["temp"]}', color=0x000000, scale=2))
    current_temp.append(Label(terminalio.FONT, text='o', y=-6, color=0x000000, scale=1))
    current_temp.y = 29 + 35  # 35 is half the tile_height
    current_temp.x = horizontal_center(start=10, end=today_icon.x, width=current_temp.width)

    uv = Label(terminalio.FONT, text=f'UV:{today["uvi"]} H:{today["humidity"]}%', color=0x000000, scale=2)
    uv.y = 128 - uv.height//2 - 5
    uv.x = horizontal_center(end=today_panel_width, width=uv.width*uv.scale)

    today_high = HBoxLayout()
    today_high.append(Label(terminalio.FONT, text=f'{today["max"]}', color=0x000000, scale=2))
    today_high.append(Label(terminalio.FONT, text='o', y=-6, color=0x000000, scale=1))
    today_high.x = horizontal_center(start=today_icon.x+70, end=today_panel_width, width=today_high.width)
    today_high.y = 29 + today_high.height//2 + 12

    today_low = HBoxLayout()
    today_low.append(Label(terminalio.FONT, text=f'{today["min"]}', color=0x000000, scale=2))
    today_low.append(Label(terminalio.FONT, text='o', y=-6, color=0x000000, scale=1))
    today_low.x = horizontal_center(start=today_icon.x+70, end=today_panel_width, width=today_low.width)
    today_low.y = 29 + 70 - today_low.height//2 - 12

    today_icon[0] = ICON_MAP.index(today['icon'][:2])

    magtag.splash.append(current_temp)
    magtag.splash.append(uv)
    magtag.splash.append(today_high)
    magtag.splash.append(today_low)
    magtag.splash.append(today_icon)

def display_forecasts(forecasts):
    # passed in forcast data dict
    # GridLayout used to position the data
    # GridLayout requires postioned objects have a width attribute, HBoxLayout is used.
    days = ("M", "T", "W", "T", "F", "S", "S")
    day_index = (RTC().datetime.tm_wday + 1) % 7

    forecast_layout = GridLayout(x=today_panel_width, y=0, width=126, height=128,
                                 grid_size=(1, 4), cell_padding=0,
                                 divider_lines=False, cell_anchor_point=(0, 1))

    for i, row in enumerate(forecasts):
        weather_icon = TileGrid(icons_small_bmp, pixel_shader=icons_small_pal,
                                x=0, y=-8, width=1, height=1,
                                tile_width=20, tile_height=20)
        weather_icon[0] = ICON_MAP.index(row['icon'][:2])

        group = HBoxLayout()
        group.append(Label(terminalio.FONT, text=f'{days[day_index]} ', color=0x000000, scale=1))
        day_index = (day_index + 1) % 7
        group.append(weather_icon)
        group.append(Label(terminalio.FONT, text=' ', color=0x000000, scale=1))
        group.append(Label(terminalio.FONT, text=f'{row["min"]}', color=0x000000, scale=2))
        group.append(Label(terminalio.FONT, text='o', y=-6, color=0x000000, scale=1))
        group.append(Label(terminalio.FONT, text=f'/{row["max"]}', color=0x000000, scale=2))
        group.append(Label(terminalio.FONT, text='o', y=-6, color=0x000000, scale=1))
        forecast_layout.add_content(cell_content=group, grid_position=(0, i), cell_size=(1,1))
    magtag.splash.append(forecast_layout)

def update_display(p_ram): # # pass in the PersistentRam object
    w_data = p_ram.weather_data
    display_todays_weather(w_data['today'])
    display_forecasts(w_data['forecast'])
    display_time_day()
    magtag.refresh()

def get_time():
    try:
        magtag.network.get_local_time()  # updates the RTC
    except (OSError, RuntimeError, HttpError) as e:
        print(f'Error {e}') # if fails time will continut to come from the RTC

def get_weather(p_ram):  # pass in the PersistentRam object
    url = (f'https://api.openweathermap.org/data/3.0/onecall?lat={secrets["openweather_lat"]}' +
       f'&lon={secrets["openweather_lon"]}&exclude=minutely,hourly,alerts&units=imperial' +
       f'&appid={secrets["openweather_token"]}')
    try:
        w_str = magtag.fetch(url)
    except (OSError, RuntimeError, HttpError) as e:
        print(f'Error {e}')
        # failure to update weather, maintain state
        magtag.exit_and_deep_sleep(60)  # wait one minute and retry
    w_data = json.loads(w_str)
    fw_data = filter_weather_data(w_data)
    p_ram.weather_data = fw_data # write the weather

# There are 4 states in the program initialize ('I') update ('U'), time ('T') and weather ('W')
# In the initialize state, the network is enabled, the time and weather data is collected
# from the network.  Data is displayed, the state is set to update time.
# The board then sleeps until it is time to update the clock (min boundry).

# In the update state the clock display is updated every minute using the RTC. The board sleeps for 60 seconds.


pr = PersistentRam()
# pr.state = 'I'
print(f'App State: {pr.state}')

if pr.state == 'U':  # Update time
    start_time = time.monotonic()
    update_display(pr) # update time
    now = RTC().datetime
    if now.tm_hour in range(6, 20) and now.tm_min in (1, 31):  # update weather  every 30 min from network from 6am to 7pm
        pr.state = 'W'
    elif now.tm_hour in range(20, 24 ) and now.tm_min == 1: # update weather every hour from 8 to 11pm, no weather updates after 11pm until 6am
        pr.state = 'W'
    elif now.tm_hour in range(0, 24, 3) and now.tm_min == 7: # update time every 3 hours at 7 min past the hour
        pr.state = 'T'
    duration = time.monotonic() - start_time
    magtag.exit_and_deep_sleep(58 - duration)  # results in a 60 second wait

elif pr.state == 'W':  # Update weather data
    start_time = time.monotonic()
    magtag.network.enabled=True
    get_weather(pr)
    magtag.network.enabled=False
    update_display(pr)
    pr.state = 'U'
    duration = time.monotonic() - start_time
    magtag.exit_and_deep_sleep(58 - duration) # results in a 60 second wait

elif pr.state == 'T': # update the time
    start_time = time.monotonic()
    magtag.network.enabled=True
    get_time()
    magtag.network.enabled=False
    update_display(pr)
    pr.state = 'U'
    duration = time.monotonic() - start_time
    magtag.exit_and_deep_sleep(58 - duration) # results in a 60 second wait

elif pr.state == 'I':   # Get time and data from network
    magtag.network.enabled=True
    get_time()
    get_weather(pr)
    magtag.network.enabled=False
    update_display(pr)
    pr.state = 'U'
    magtag.exit_and_deep_sleep((120 - 2 - RTC().datetime.tm_sec) % 60)  # set so time updates at the min change
else:
    raise ValueError('Invalid application state')






