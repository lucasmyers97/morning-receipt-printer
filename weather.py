import json
from urllib.request import urlopen
import geocoder
import datetime

from escpos.printer import Usb

date_input_format = '%Y-%m-%dT%X%z'
date_output_format = '%A %B %d'

def print_json(file):
    print(json.dumps(file, indent=2))

def main():

    # get latitude & longitude from ip
    g = geocoder.ip('me')
    lat, lon = g.latlng

    # query weather service about forecast, make JSON
    location_url = 'https://api.weather.gov/points/{},{}'
    with urlopen(location_url.format(lat, lon)) as response:
        location_str = response.read().decode('utf-8')
    location_json = json.loads( location_str )

    forecast_url = location_json['properties']['forecast']
    with urlopen(forecast_url) as response:
        forecast_str = response.read().decode('utf-8')
    forecast_json = json.loads( forecast_str )

    # get data from JSON
    forecast_current = forecast_json['properties']['periods'][0]
    forecast_current_time = forecast_current['name'].upper()

    forecast_later = forecast_json['properties']['periods'][1]
    forecast_later_time = forecast_later['name'].upper()

    date = datetime.datetime.strptime(forecast_current['startTime'], 
                                      date_input_format)
    date_string = date.strftime(date_output_format)

    temp = ( str(forecast_current['temperature']) 
             + forecast_current['temperatureUnit'] )
    wind = forecast_current['windSpeed']
    short_forecast = forecast_current['shortForecast']
    detailed_forecast = ".\n".join( forecast_current['detailedForecast'].split('. ') )

    later_temp = ( str(forecast_later['temperature']) 
                     + forecast_later['temperatureUnit'] )
    later_short_forecast = forecast_later['shortForecast']

    # Format the output
    print(date_string)
    print('='*42)
    print('{}: {} {}'.format(forecast_current_time, temp, wind))
    print(short_forecast)
    print()

    print(detailed_forecast)
    print()

    print('{}: {}'.format(forecast_later_time, later_temp))
    print(later_short_forecast)

    print('='*42)

    # p = Usb(0x04b8, 0x0202, 0, profile="TM-T88V")
    # p.text(date_string + '\n')
    # p.text('='*42 + '\n')
    # p.text('TODAY: {} {}\n'.format(temp, wind))
    # p.text(short_forecast + '\n')
    # p.text('\n')
    #
    # p.text(detailed_forecast + '\n')
    # p.text('\n')
    #
    # p.text('TONIGHT: {}\n'.format(tonight_temp))
    # p.text(tonight_short_forecast + '\n')
    #
    # p.text('='*42 + '\n')
    #
    # p.cut()

if __name__ == '__main__':
    main()
