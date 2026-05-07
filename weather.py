"""
Note: for Epson TM-T88V, product id and vendor id are typically: 0x04b8:0x0202
"""

import json
from urllib.request import urlopen
import geocoder
import datetime
import argparse

from PIL import Image
import requests
from io import BytesIO

from escpos.printer import Usb

date_input_format = '%Y-%m-%dT%X%z'
date_output_format = '%A %B %d'

desc = """Get weather forecast from NWS.
Format nicely, then print to terminal or a receipt.
"""

def get_commandline_args():
    parser = argparse.ArgumentParser(
                        prog='GetWeatherForecast',
                        description=desc)

    parser.add_argument('--print_to_receipt',
                        action='store_true',
                        help='Whether to print to receipt -- alternative is to terminal.') 
    parser.add_argument('--vendor_id',
                        type=lambda x: int(x, 0),
                        help='Vendor ID of printer. Check `lsusb` for the first part of a number formatted as xxxx:xxxx')
    parser.add_argument('--product_id',
                        type=lambda x: int(x, 0),
                        help='Product ID of printer. Check `lsusb` for the second part of a number formatted as xxxx:xxxx')
    parser.add_argument('--printer_model',
                        help='Model of the printer (see Python escpos for formatting details)')

    args = parser.parse_args()

    return args.print_to_receipt, args.vendor_id, args.product_id, args.printer_model


def get_image_from_link(link: str) -> Image.Image:
    """
    Gets image from link as Pillow image.
    Resizes so that it's as large as possible on the receipt printer.
    """
    response = requests.get(link)
    im = Image.open(BytesIO(response.content))
    ratio = 384 / im.width
    (width, height) = (int(ratio * im.width), int(ratio * im.height))
    return im.resize((width, height))


class Forecast:
    def __init__(self, forecast):
        self.time = forecast['name'].upper()
        date = datetime.datetime.strptime(forecast['startTime'], 
                                          date_input_format)
        self.date = date.strftime(date_output_format)
        self.temp = ( str(forecast['temperature']) + forecast['temperatureUnit'] )
        self.wind = forecast['windSpeed']
        self.short_forecast = forecast['shortForecast']
        self.detailed_forecast = ".\n".join( forecast['detailedForecast'].split('. ') )
        self.icon = get_image_from_link(forecast['icon'])


def print_forecast_to_terminal(forecast_current, forecast_later):

    print(forecast_current.date)
    print('='*42)
    print('{}: {} {}'.format(forecast_current.time, 
                             forecast_current.temp, 
                             forecast_current.wind))
    print(forecast_current.short_forecast)
    print()

    print(forecast_current.detailed_forecast)
    print()

    print('{}: {}'.format(forecast_later.time, forecast_later.temp))
    print(forecast_later.short_forecast)

    print('='*42)

    forecast_current.icon.show()
    forecast_later.icon.show()


def print_forecast_to_receipt(forecast_current, forecast_later,
                              vendor_id, product_id, printer_model):

    p = Usb(vendor_id, product_id, profile=printer_model)

    p.image(forecast_current.icon, center=True)
    p.ln()

    p.text(forecast_current.date + '\n')
    p.text('='*42 + '\n')
    p.text('{}: {} {}\n'.format(forecast_current.time,
                                forecast_current.temp,
                                forecast_current.wind))
    p.text(forecast_current.short_forecast + '\n')
    p.text('\n')

    p.text(forecast_current.detailed_forecast + '\n')
    p.text('\n')

    p.text('{}: {}\n'.format(forecast_later.time, forecast_later.temp))
    p.text(forecast_later.short_forecast + '\n')

    p.text('='*42 + '\n')

    p.image(forecast_later.icon, center=True)

    p.cut()


def print_json(file):
    print(json.dumps(file, indent=2))


def main():

    print_to_receipt, vendor_id, product_id, printer_model = get_commandline_args()

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
    forecast_current = Forecast(forecast_json['properties']['periods'][0])
    forecast_later = Forecast(forecast_json['properties']['periods'][1])

    if print_to_receipt:
        print_forecast_to_receipt(forecast_current, forecast_later,
                                  vendor_id, product_id, printer_model)

    else:
        print_forecast_to_terminal(forecast_current, forecast_later)


if __name__ == '__main__':
    main()
