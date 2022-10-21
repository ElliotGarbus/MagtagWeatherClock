# MagtagWeatherClock
Displays the time, day, current weather and a 4-day forecast.

Pressing the D11 button forces an update of the weather and time.

To extend battery life:
- Time is updated every 3 hours to maintain acceptable accuracy.  The RTC on the ESP32-S2 does not keep very accurate time.
- Weather is updated every 30 min between 6am and 7pm
- Weather is updated hourly from 8 to 11pm
- Weather is NOT updated after 11am, until 6:01 am

The Hardware is the Adafruit Magtag see: https://www.adafruit.com/product/4800
![IMG_7889](https://user-images.githubusercontent.com/39632979/191172528-971b6b53-364a-4444-85c1-99a2eb8f6f29.jpg)
