from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

from PIL import Image
import requests
from io import BytesIO

from poem_parsing_tools import parse_browser_poem_info, parse_browser_poem_text

from escpos.printer import Usb

def navigate_to_poem_of_the_day():
    poem_of_the_day_url = 'https://www.poetryfoundation.org/poems/poem-of-the-day'
    options = Options()
    # options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
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


def main():

    line_width = 42
    printer = Usb(0x04b8, 0x0202, 0, profile="TM-T88V")
    driver = webdriver.Firefox()

    urls = ['https://www.poetryfoundation.org/poetrymagazine/poems/1779626/ode-on-humidity',
            'https://www.poetryfoundation.org/poems/158012/watching-my-mother',
            'https://www.poetryfoundation.org/poetrymagazine/poems/58584/harolds-chicken-shack-86',
            'https://www.poetryfoundation.org/poems/55028/breakfast-with-thom-gunn',
            'https://www.poetryfoundation.org/poems/47100/tree-56d227515c386',
            'https://www.poetryfoundation.org/poetrymagazine/poems/1779608/i',
            'https://www.poetryfoundation.org/poetrymagazine/poems/58643/the-outstretched-earth',
            'https://www.poetryfoundation.org/poetrymagazine/poems/54910/for-you-anthophilous-lover-of-flowers',
            'https://www.poetryfoundation.org/poetrymagazine/poems/1779624/smokes',
            'https://www.poetryfoundation.org/poems/49932/no-moon-floods-the-memory-of-that-night',
            'https://www.poetryfoundation.org/poetrymagazine/poems/1600382/descendant',
            'https://www.poetryfoundation.org/poems/53907/haiku-journey',
            'https://www.poetryfoundation.org/poems/56376/the-good-life',
            'https://www.poetryfoundation.org/poetrymagazine/poems/160485/open-and-closed-spaces',
            'https://www.poetryfoundation.org/poetrymagazine/poems/1682858/flipping-the-bird',
            'https://www.poetryfoundation.org/poems/48393/north-56d22998bff6c',
            'https://www.poetryfoundation.org/poetrymagazine/poems/1779562/staying-after',
            'https://www.poetryfoundation.org/poetrymagazine/poems/147619/annotations-for-a-memorial',
            'https://www.poetryfoundation.org/poems/54683/you-also-nightingale',
            'https://www.poetryfoundation.org/poetrymagazine/poems/90975/despite-my-efforts-even-my-prayers-have-turned-into-threats',
            'https://www.poetryfoundation.org/poetrymagazine/poems/1779630/enter-book',
            'https://www.poetryfoundation.org/poems/48397/infidelity-56d2299b7246c',
            'https://www.poetryfoundation.org/poems/54587/spring-song-56d2351b45223',
            'https://www.poetryfoundation.org/poetrymagazine/poems/55948/three-poems-after-yannis-ritsos',
            'https://www.poetryfoundation.org/poetrymagazine/poems/58786/sissieretta-jones',
            'https://www.poetryfoundation.org/poetrymagazine/poems/42364/on-leaving-the-bachelorette-brunch',
            'https://www.poetryfoundation.org/poetrymagazine/poems/148099/everything-5bb78da98dce1',
            'https://www.poetryfoundation.org/poems/151342/cinco-de-mayo',
            'https://www.poetryfoundation.org/poems/147193/a-blessing-5b2a78fed2c23c',
            ]

    for url in urls:
        driver.get(url)

        title, authors, preface, image_links = parse_browser_poem_info(driver, line_width)
        poem_lines = parse_browser_poem_text(driver, line_width)

        print_border(printer, line_width)
        print_poem_info(printer, title, authors, preface)
        print_poem_body(printer, poem_lines)
        print_border(printer, line_width)

        for link in image_links:
            response = requests.get(link)
            im = Image.open(BytesIO(response.content))
            ratio = 512 / im.width
            (width, height) = (int(ratio * im.width), int(ratio * im.height))
            im_resized = im.resize((width, height))

            printer.image(im_resized)

        printer.cut()

    driver.close()

if __name__ == '__main__':
    main()
