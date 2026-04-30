from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import re

class TextLine:
    def __init__(self, style):
        self.html = ''
        self.style = style.split('; ')

    def add_style(self, style):
        self.style += style.split('; ')

    def add_html(self, html):
        self.html = html

    def strip_html(self):
        """
        Newlines and `<br>` tags happen to be superfluous in the poems.
        `&amp;` and `&nbsp` get converted to regular characters.
        `<i></i>` converted to `<em></em>` for bolding consistency.
        """
        self.html = re.sub('\n ', '', self.html)
        self.html = re.sub('<br>', '', self.html)
        self.html = re.sub('&amp;', '&', self.html)
        self.html = re.sub('&nbsp;', ' ', self.html)
        self.html = re.sub('<i>', '<em>', self.html)
        self.html = re.sub('</i>', '</em>', self.html)

    def strip_style(self):
        """
        These are just the regular style tags that every line in the poem has.
        Not necessary to keep when figuring out leading whitespace.
        """
        self.style.remove('text-indent: -1em')
        self.style.remove('padding-left: 1em;')

    def add_whitespace(self, line_width):
        """
        These are the two style tags I have seen which pad or justify the
        poem lines. 
        The added whitespace attempts to emulate the html formatting with plain
        text.
        """
        matches = [re.search('padding-left: (\\d+)%;', style) for style in self.style]
        if matches and matches[0]:
            num_spaces = int( float(matches[0].group(1)) / 100 * line_width )
            self.html = num_spaces * ' ' + self.html

        matches = [re.search('text-align:\\s*right', style) for style in self.style]
        if matches and matches[0]:
            num_spaces = line_width - len(self.html)
            self.html = num_spaces * ' ' + self.html

def parse_browser_poem_info(driver):
    """
    Given a webdriver `driver` THAT IS ALREADY NAVIGATED TO THE POEM WEBPAGE, 
    this method retrieves relevant info from the webpage, including the title,
    authors, and preface (e.g. "Translated from..." or other relevant quotes 
    before the poem text) as plain text.

    Parameters
    ----------
    driver: Selenium webdriver
        Webdriver that is already navigated to the poem url via driver.get(url).

    Returns
    -------
    title : string
        Title of the poem.
    authors : array of strings
        Author(s) of the poem with "By" or "Translated By" appended to the
        beginning, depending on contribution.
    preface_lines : array of strings or None
        Lines of the preface (e.g. "Translated from...", etc.) if there is one.

    Note about poetryfoundation webpages: mainContent is the ID of everything
    relevant to specific poem (i.e. not the top bar, recommended on bottom, 
    etc.). There are nested `header` tags containing the title and authors,
    so it doesn't matter which we retrieve. The title has class `type-gamma`
    and the authors `type-kappa`, the only such in the specific header.
    Finally, the preface is hard to pin down but seems to consistently have
    class `type-paragraph-sm`. It contains newlines for formatting.
    """
    main_content = driver.find_element(By.ID, 'mainContent')

    header = main_content.find_element(By.TAG_NAME, 'header')
    title = header.find_element(By.CLASS_NAME, 'type-gamma').text
    authors = [author.text for author in header.find_elements(By.CLASS_NAME, 'type-kappa')]

    try:
        preface = main_content.find_element(By.CLASS_NAME, 'type-paragraph-sm').text
        preface_lines = [line for line in preface.split('\n')]
    except NoSuchElementException:
        preface_lines = None

    return title, authors, preface_lines


def parse_browser_poem_text(driver):
    """
    Given a webdriver `driver` THAT IS ALREADY NAVIGATED TO THE POEM WEBPAGE, 
    this method retrieves the lines of the poem in plain text, including
    limited formatting (like indenting or justification). 
    Note that `<em>` tags are left in for purposes of italicizing or bolding.

    Parameters
    ----------
    driver : Selenium webdriver
        Webdriver which is already navigated to the poem page via driver.get(url).

    Returns
    -------
    text_lines : array of strings
        Lines of the poem, already formatted with extra whitespace.

    Note about poetryfoundation webpages: the actual poem has the class name
    `poem-body`. The lines of the poem are then individual `<div>` tags which
    are immediately under the poem-body tags. Inside these `<div>` tags, there
    may also be `<span>` or `<div>` tags whose style specifies padding,
    justification, etc. which is recorded in the TextLine objects.

    There are superfluous `<br>` tags and newlines, which we strip via the
    TextLine class. Additionally, `&amp;` and `&nbsp;` elements are converted
    to plain text.

    Finally, leading whitespace is added based on justification and padding
    style tags.
    """
    poem_body = driver.find_element(By.CLASS_NAME, 'poem-body')
    poem_lines = poem_body.find_elements(By.XPATH, '*')

    text_lines = []
    for line in poem_lines:
        text_line = TextLine(line.get_attribute('style'))

        spans = line.find_elements(By.XPATH, 'span')
        divs = line.find_elements(By.XPATH, 'div')
        if spans:
            text_line.add_style(spans[0].get_attribute('style'))
            text_line.add_html(spans[0].get_attribute('innerHTML'))

        elif divs:
            text_line.add_style(divs[0].get_attribute('style'))
            text_line.add_html(divs[0].get_attribute('innerHTML'))

        else:
            text_line.add_html(line.get_attribute('innerHTML'))

        text_line.strip_html()
        text_line.strip_style()
        text_lines.append(text_line)

    line_width = 0
    for line in text_lines:
        line_width = max( len(line.html), line_width )

    for line in text_lines:
        line.add_whitespace(line_width)

    return [line.html for line in text_lines]

def main():

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

    driver = webdriver.Firefox()
    for url in urls:

        driver.get(url[0])

        title, authors, preface = parse_browser_poem_info(driver)
        poem_lines = parse_browser_poem_text(driver)

        print(title)
        for author in authors:
            print(author)

        print()

        if preface:
            for line in preface:
                print(4*' ', line, sep='')

            print()
            print()

        for line in poem_lines:
            print(line)

        print(60*'=')

    driver.close()


if __name__ == '__main__':
    main()
