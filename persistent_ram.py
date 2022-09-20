"""
PersistentRam
provides convenient access to the alarm.sleep_memory.
The PersistentRam stores the current state of the program (I, U or W) and
the current weather data from the last time the network was accessed.

Memory map:
Location    Content
0           state - either a U or I
1:5         length - the length of the JSON string that holds the weather data
5:          the data

"""
import alarm
import struct
import json


class PersistentRam:
    @property
    def state(self):
        # states are 'I' for initialize and 'U' for update, W for weather, T for time
        if chr(alarm.sleep_memory[0]) in ['I', 'U', 'W', 'T']:
            return chr(alarm.sleep_memory[0])
        else:
            alarm.sleep_memory[0] = ord('I')
            return 'I'

    @state.setter
    def state(self, value):
        if value not in ['I', 'U', 'W', 'T']:
            raise ValueError('State value must be "I", "U", "W" or "T"')
        alarm.sleep_memory[0] = ord(value)

    @property
    def weather_data(self):
        # returns the weather data as a dict
        # retrieve the length of the weather data string
        # retrieve the weather data string, convert to a dict and return
        wd_len = struct.unpack('I', alarm.sleep_memory[1:5])[0]
        wd_str = alarm.sleep_memory[5:5+wd_len].decode()
        return json.loads(wd_str)

    @weather_data.setter
    def weather_data(self, wd_json):
        # Convert the JSON dict to a string
        # save the length of the string and the string of weather data
        wd_str = json.dumps(wd_json)
        wd_len = len(wd_str)
        if wd_len > len(alarm.sleep_memory) - 5:
            raise ValueError('Length of weather data exceeds available size')
        alarm.sleep_memory[1:5] = struct.pack('I', wd_len) # used to convert bytes <-> unsigned int
        alarm.sleep_memory[5:wd_len+5] = bytearray(wd_str.encode('ascii'))


