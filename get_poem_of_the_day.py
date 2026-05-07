from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By

from PIL import Image
import requests
from io import BytesIO
import argparse
import sys
import traceback

from poem_parsing_tools import TextLine, parse_browser_poem_info, parse_browser_poem_text

from escpos.printer import Usb

desc = """Gets poem-of-the-day from poetryfoundation, formats 
and prints it using a receipt printer, 
including author headshot at the end of the poem.
"""

def get_commandline_args() -> tuple[str, int, int, str, int]:
    """
    Parses argument inputs from the commandline (only `driver_path` in this
    case).
    """
    parser = argparse.ArgumentParser(
                        prog='GetPoemOfTheDay',
                        description=desc)

    parser.add_argument('--driver_path',
                        default='',
                        help='Path of geckodriver for webscraping (typically only needed for ARM devices)') 
    parser.add_argument('--vendor_id',
                        type=lambda x: int(x, 0),
                        help='Vendor ID of printer. Check `lsusb` for the first part of a number formatted as xxxx:xxxx')
    parser.add_argument('--product_id',
                        type=lambda x: int(x, 0),
                        help='Product ID of printer. Check `lsusb` for the second part of a number formatted as xxxx:xxxx')
    parser.add_argument('--printer_model',
                        help='Model of the printer (see Python escpos for formatting details)')
    parser.add_argument('--line_width',
                        type=int,
                        help='Width of receipt line')

    args = parser.parse_args()

    return args.driver_path, args.vendor_id, args.product_id, args.printer_model, args.line_width


def create_driver(driver_path: str) -> webdriver.Firefox:
    """
    Creates Selenium webdriver using a Firefox browser.
    For the Raspberry Pi a custom geckodriver executable which was compiled for
    ARM architecture needs to be specified, hence the `driver_path` parameter.
    """
    options = Options()
    options.add_argument('--headless')
    service = Service(driver_path)

    driver = webdriver.Firefox(options=options, service=service)

    return driver


def navigate_to_poem_of_the_day(driver: webdriver.Firefox) -> webdriver.Firefox:
    """
    Given a Selenium webdriver `driver`, navigate 
    """
    poem_of_the_day_url = 'https://www.poetryfoundation.org/poems/poem-of-the-day'
    driver.get(poem_of_the_day_url)

    read_more = driver.find_element(By.LINK_TEXT, 'Read More')
    read_more_link = read_more.get_attribute('href')

    if not read_more_link:
        raise ValueError('Could not find `Read More` link')

    driver.get(read_more_link)

    return driver


def print_border(printer: Usb, line_width: int):
    """
    Prints top (or bottom) border of receipt poem.
    Just a `line_width` number of '=' characters and a newline.
    """
    printer.text(line_width*'=' + '\n')


def print_poem_info(printer: Usb, title: str, authors: list[str], preface: list[str] | None):
    """
    Prints formatted `title`, list of `authors`, and `preface` for the poem
    to the receipt printer.
    """
    printer.text(title + '\n')
    for author in authors:
        printer.text(author + '\n')

    printer.ln()

    if preface:
        printer.set(bold=True)
        for line in preface:
            text = ('\n' + 4*' ').join(line)
            printer.text(4*' ' + text + '\n')
        printer.set(bold=False)

        printer.ln(2)


def print_poem_body(printer: Usb, poem_lines: list[TextLine]):
    """
    Prints formatted poem body to receipt printer given a list of `TextLine`
    objects `poem_lines`, which contain the text of each line, as well as
    indices corresponding to italics (which will be bolded in the actual
    receipt). 
    """
    for line in poem_lines:
        text = line.text
        bold_char_end = 0
        for index in line.em_indices:
            bold_char_start = index[0]
            printer.text(text[bold_char_end:bold_char_start])

            bold_char_end = index[1]
            printer.set(bold=True)
            printer.text(text[bold_char_start:bold_char_end])
            printer.set(bold=False)

        printer.text(text[bold_char_end:] + '\n')


def print_image_from_link(printer: Usb, link: str):
    """
    Prints image to receipt printer, given an internet link to that image.
    """
    response = requests.get(link)
    im = Image.open(BytesIO(response.content))
    ratio = 512 / im.width
    (width, height) = (int(ratio * im.width), int(ratio * im.height))
    im_resized = im.resize((width, height))

    printer.image(im_resized)


def main():

    line_width = 42
    driver_path, vendor_id, product_id, printer_model, line_width  = get_commandline_args()
    printer = Usb(vendor_id, product_id, profile=printer_model)


    driver = create_driver(driver_path)
    try: 
        driver = navigate_to_poem_of_the_day(driver)
        title, authors, preface, image_links = parse_browser_poem_info(driver, line_width)
        poem_lines = parse_browser_poem_text(driver, line_width)

        print_border(printer, line_width)
        print_poem_info(printer, title, authors, preface)
        print_poem_body(printer, poem_lines)
        print_border(printer, line_width)

        for link in image_links:
            print_image_from_link(printer, link)

        printer.cut()

        driver.quit()
    except Exception as e:
        driver.quit()
        traceback.print_tb(e.__traceback__, file=sys.stderr)
        print(e, file=sys.stderr)


if __name__ == '__main__':
    main()
