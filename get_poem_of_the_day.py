from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By

from PIL import Image
import requests
from io import BytesIO
import argparse

from poem_parsing_tools import parse_browser_poem_info, parse_browser_poem_text

from escpos.printer import Usb

desc = """Gets poem-of-the-day from poetryfoundation, formats 
and prints it using a receipt printer, 
including author headshot at the end of the poem.
"""

def get_commandline_args():
    parser = argparse.ArgumentParser(
                        prog='GetPoemOfTheDay',
                        description=desc)

    parser.add_argument('--driver_path',
                        default='',
                        help='Path of geckodriver for webscraping (typically only needed for ARM devices)') 

    args = parser.parse_args()

    return args.driver_path


def navigate_to_poem_of_the_day(driver_path):
    poem_of_the_day_url = 'https://www.poetryfoundation.org/poems/poem-of-the-day'
    options = Options()
    options.add_argument('--headless')

    service = Service(driver_path)
    driver = webdriver.Firefox(options=options, service=service)
    driver.get(poem_of_the_day_url)

    read_more = driver.find_element(By.LINK_TEXT, 'Read More')
    read_more_link = read_more.get_attribute('href')

    if not read_more_link:
        raise ValueError('Could not find `Read More` link')

    driver.get(read_more_link)

    return driver

def print_border(printer, line_width):
    printer.text(line_width*'=' + '\n')


def print_poem_info(printer, title, authors, preface):
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


def print_poem_body(printer, poem_lines):
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


def print_image_from_link(printer, link):
        response = requests.get(link)
        im = Image.open(BytesIO(response.content))
        ratio = 512 / im.width
        (width, height) = (int(ratio * im.width), int(ratio * im.height))
        im_resized = im.resize((width, height))

        printer.image(im_resized)


def main():

    line_width = 42
    printer = Usb(0x04b8, 0x0202, 0, profile="TM-T88V")

    driver_path = get_commandline_args()

    driver = navigate_to_poem_of_the_day(driver_path)

    title, authors, preface, image_links = parse_browser_poem_info(driver, line_width)
    poem_lines = parse_browser_poem_text(driver, line_width)

    print_border(printer, line_width)
    print_poem_info(printer, title, authors, preface)
    print_poem_body(printer, poem_lines)
    print_border(printer, line_width)

    for link in image_links:
        print_image_from_link(printer, link)

    printer.cut()

    driver.close()

if __name__ == '__main__':
    main()
