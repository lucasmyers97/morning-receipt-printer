from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from poem_parsing_tools import parse_browser_poem_info, parse_browser_poem_text
import re
import time

from escpos.printer import Usb

def main():

    line_width = 42

    urls = [
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1779626/ode-on-humidity', 'ode-on-humidity'],
            ['https://www.poetryfoundation.org/poems/158012/watching-my-mother', 'watching-my-mother'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/58584/harolds-chicken-shack-86', 'harolds-chicken-shack-86'],
            ['https://www.poetryfoundation.org/poems/55028/breakfast-with-thom-gunn', 'breakfast-with-thom-gunn'],
            ['https://www.poetryfoundation.org/poems/47100/tree-56d227515c386', 'tree-56d227515c386'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1779608/i', 'i'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/58643/the-outstretched-earth', 'the-outstretched-earth'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/54910/for-you-anthophilous-lover-of-flowers', 'for-you-anthophilous-lover-of-flowers'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1779624/smokes', 'smokes'],
            ['https://www.poetryfoundation.org/poems/49932/no-moon-floods-the-memory-of-that-night', 'no-moon-floods-the-memory-of-that-night'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1600382/descendant', 'descendant'],
            ['https://www.poetryfoundation.org/poems/53907/haiku-journey', 'haiku-journey'],
            ['https://www.poetryfoundation.org/poems/56376/the-good-life', 'the-good-life'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/160485/open-and-closed-spaces', 'open-and-closed-spaces'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1682858/flipping-the-bird', 'flipping-the-bird'],
            ['https://www.poetryfoundation.org/poems/48393/north-56d22998bff6c', 'north-56d22998bff6c'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1779562/staying-after', 'staying-after'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/147619/annotations-for-a-memorial', 'annotations-for-a-memorial'],
            ['https://www.poetryfoundation.org/poems/54683/you-also-nightingale', 'you-also-nightingale'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/90975/despite-my-efforts-even-my-prayers-have-turned-into-threats', 'despite-my-efforts-even-my-prayers-have-turned-into-threats'],
            ['https://www.poetryfoundation.org/poetrymagazine/poems/1779630/enter-book', 'enter-book'],
            ['https://www.poetryfoundation.org/poems/48397/infidelity-56d2299b7246c', 'infidelity'],
            ['https://www.poetryfoundation.org/poems/54587/spring-song-56d2351b45223', 'spring-song']
            ]

    urls = [['https://www.poetryfoundation.org/poetrymagazine/poems/58584/harolds-chicken-shack-86', 'harolds-chicken-shack-86']]

    p = Usb(0x04b8, 0x0202, 0, profile="TM-T88V")

    options = Options()
    options.add_argument('--headless')
    driver = webdriver.Firefox(options=options)
    for url in urls:
        driver.get(url[0])

        time.sleep(5)

        title, authors, preface = parse_browser_poem_info(driver, line_width)
        poem_lines = parse_browser_poem_text(driver, line_width)

        p.text(line_width*'=' + '\n')

        p.text(title + '\n')
        for author in authors:
            p.text(author + '\n')

        p.ln()

        if preface:
            p.set(bold=True)
            for line in preface:
                text = ('\n' + 4*' ').join(line)
                p.text(4*' ' + text + '\n')
            p.set(bold=False)

            p.ln(2)

        for line in poem_lines:
            text = line.text
            bold_char_end = 0
            for index in line.em_indices:
                bold_char_start = index[0]
                p.text(text[bold_char_end:bold_char_start])

                bold_char_end = index[1]
                p.set(bold=True)
                p.text(text[bold_char_start:bold_char_end])
                p.set(bold=False)

            p.text(text[bold_char_end:] + '\n')

        p.text(line_width*'=' + '\n')
        p.cut()

        # print(title)
        # for author in authors:
        #     print(author)
        #
        # print()
        #
        # if preface:
        #     print('\033[1m', end='')
        #     for line in preface:
        #         text = ('\n' + 4*' ').join(line)
        #         print(4*' ', text, sep='')
        #     print('\033[0m', end='')
        #
        #     print()
        #     print()
        #
        # for line in poem_lines:
        #     text = line.text
        #     bold_char_end = 0
        #     for index in line.em_indices:
        #         bold_char_start = index[0]
        #         print(text[bold_char_end:bold_char_start], end='')
        #
        #         bold_char_end = index[1]
        #         print('\033[1m', end='')
        #         print(text[bold_char_start:bold_char_end], end='')
        #         print('\033[0m', end='')
        #
        #     print(text[bold_char_end:])
        #
        # print(line_width*'=')

    driver.close()

if __name__ == '__main__':
    main()
