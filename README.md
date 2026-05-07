# Morning Receipt Printer

## Basic Info

Wake up to a freshly printed receipt with all the info that you need to start your day!
Right now this project is able to retrieve and format a weather report, and the poem of the day from poetryfoundation.org.
It can format and print this info either to the terminal or a receipt printer.
This also includes images of icons for the weather, and headshots of the poets.
Different poems (not just the poem of the day!) may be printed by providing a link to the poem on poetryfoundation.org.

This can all be run from a Raspberry Pi 2, although extra setup is needed to allow a Selenium webdriver to run on ARMv7 architecture.

## Installation

``` bash
# clone repository onto your machine
git clone https://github.com/lucasmyers97/morning-receipt-printer.git

# Go to repository folder
cd morning-receipt-printer

# Create virtual environment for repository
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies in virtual environment
pip install -r requirements.txt
```
If you need to deactivate the virtual environment:
``` bash
deactivate
```

## Usage

To get into the virtual environment
``` bash
cd path/to/morning-receipt-printer
source venv/bin/activate
```

To print the weather forecast to terminal:
``` bash
python3 get_weather_forecast.py --line_width 50
```
To print the poem of the day to the terminal:
``` bash
python3 get_poem_of_the_day.py --line_width 50
```
To print any other poem to the terminal:
``` bash
python get_poem_of_the_day.py --line_width 42 --poem_url https://www.poetryfoundation.org/link/to/poem
```
(Note that you cannot just copy and past this one, you must provide a link to the poem you want).

Printing to a receipt printer is slightly more involved. 
First, plug in the printer and turn it on.
Then plug the printer into your USB (this repo currently only supports USB printing).
In the terminal type:
``` bash
lsusb
```
which should return a line corresponding to your printer:
``` bash
Bus 001 Device 087: ID 04b8:0202 Seiko Epson Corp. Interface Card UB-U05 for Thermal Receipt Printers [M129C/TM-T70/TM-T88IV]
```
The Vendor ID and Product ID are given in hex via `xxxx:xxxx`.
For my device, the Vendor ID is 04b8 (or 1208 in base 10) and the Product ID is 0202 (or 514 in base 10).
Note these numbers for your device.
Additionally, the printer model should be given on the device -- note this as well.
Mine is a `TM-T88V`.

Given these numbers for my printer, I can print the weather forecast as:
``` bash
python3 get_weather_forecast.py --print_to_receipt --vendor_id 0x04b8 --product_id 0x0202 --line_width 42 --printer_model TM-T88V
```
or the poem of the day as:
``` bash
python get_poem_of_the_day.py --line_width 42 --print_to_receipt --vendor_id 0x04b8 --product_id 0x0202 --printer_model TM-T88V
```

## Raspberry Pi 2 (ARMv7) setup

Mozilla has deprecated ARMv7 builds as of September 2018.
However, there is still an unofficial binary that one may download from [this repository](https://github.com/jamesmortensen/geckodriver-arm-binaries).
Additionally, the repository and [this page from Mozilla](https://firefox-source-docs.mozilla.org/testing/geckodriver/ARM.html) explain how to build from source, if you prefer.
I just pulled it from the repository:
``` bash
# download geckodriver binary
wget https://github.com/jamesmortensen/geckodriver-arm-binaries/releases/download/v0.34.0/geckodriver-v0.34.0-linux-armv7l.tar.gz

# download checksum for geckodriver binary
wget https://github.com/jamesmortensen/geckodriver-arm-binaries/releases/download/v0.34.0/geckodriver-v0.34.0-linux-armv7l.tar.gz.md5

# check the checksum (should say "OK")
md5sum -c geckodriver-v0.34.0-linux-armv7l.tar.gz.md5

# unzip geckodriver
tar -xvf geckodriver-v0.34.0-linux-armv7l.tar.gz

# move geckodriver binary to where you want it (usually ~/.local/bin)
mv geckodriver ~/.local/bin
```
Then, when running the `get_poem_of_the_day.py` script, you will need to provide a location to the geckodriver binary:
``` bash
python get_poem_of_the_day.py --line_width 42 --print_to_receipt --vendor_id 0x04b8 --product_id 0x0202 --printer_model TM-T88V --driver_path /home/lucas/.local/bin
```
where the `--driver_path` argument is just a global argument to where your  `geckodriver` binary lives.

## Automation suggestions

In my use case, a Raspberry Pi prints these items every morning.
To accomplish this, I created a few bash wrapper scripts, `print_weather` and `print_poem`:
``` bash
#!/bin/bash

cd ~/Documents/morning-receipt-printer
source venv/bin/activate
python3 get_weather_forecast.py --print_to_receipt --vendor_id 0x04b8 --product_id 0x0202 --line_width 42 --printer_model TM-T88V 2>> weather_error.log
```
and
``` bash
#!/bin/bash

cd ~/Documents/morning-receipt-printer
source venv/bin/activate
python get_poem_of_the_day.py --driver_path /usr/bin/geckodriver --line_width 42 --print_to_receipt --vendor_id 0x04b8 --product_id 0x0202 --printer_model TM-T88V 2>> poem_error.log
```
To make them executable, run
``` bash
chmod u+x print_weather
chmod u+x print_poem
```
Then, to automate them to run at certain frequencies, one may use `crontab`.
For example, to run once every day at 8am, one would put the following lines in `crontab` with the `crontab -e` command:
``` bash
00 08 * * * /home/lucas/.local/bin/print_weather
00 08 * * * /home/lucas/.local/bin/print_poem
```
Make sure to put the global path in its entirety -- `crontab` runs in an isolated environment, and so does not necessarily respect the `PATH` variable.
For more info on using `crontab`, [see here](https://linuxhandbook.com/crontab/).

## Future plans

I have an idea of using an old telephone answering machine to play audio if the poems have audio files (they sometimes do), but I'm unsure how to send such signals with the Pi.
Could also try to leave an actual voicemail with Google voice.

Ideally the end user would not have to know how to `ssh` into a pi, or use the commandline at all, so I'm considering adding some kind of graphical user interface.
There are cheap OLED screens w/buttons and knobs that connect to GPIO pins (or USB?) so this is a possibility. 

Open to suggestions for other things to print or other features to add!
