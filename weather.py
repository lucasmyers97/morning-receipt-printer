import json
from urllib.request import urlopen
import geocoder
import datetime

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
    forecast = forecast_json['properties']['periods'][0]
    forecast_tonight = forecast_json['properties']['periods'][1]

    date = datetime.datetime.strptime(forecast['startTime'], date_input_format)
    date_string = date.strftime(date_output_format)

    temp = str(forecast['temperature']) + forecast['temperatureUnit']
    wind = forecast['windSpeed']
    short_forecast = forecast['shortForecast']
    detailed_forecast = ".\n".join( forecast['detailedForecast'].split('. ') )

    tonight_temp = ( str(forecast_tonight['temperature']) 
                     + forecast_tonight['temperatureUnit'] )
    tonight_short_forecast = forecast_tonight['shortForecast']

    # Format the output
    print(date_string)
    print('='*30)
    print('TODAY: {} {}'.format(temp, wind))
    print(short_forecast)
    print()

    print(detailed_forecast)
    print()

    print('TONIGHT: {}'.format(tonight_temp))
    print(tonight_short_forecast)

if __name__ == '__main__':
    main()
