from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

import re
import textwrap

"""
Need to rewrite tomorrow. 
Don't even get <em> word indices.
Just get <em> character indices.
Use textwrap so that it doesn't delete any characters.
Move <em> indices when deleting or adding whitespace (should think about how to do this).
"""

class TextLine:
    def __init__(self, text, em_indices):
        self.text = text
        self.em_indices = em_indices

def delete_unprintable_characters(text):
    """
    Deletes characters which the receipt printer is not able to print.
    Replaces them with the closest character that is printable.
    """
    unprintable_characters = [('\u2009', ' '), ('\u200a', '')]
    for char in unprintable_characters:
        text = text.replace(char[0], char[1])

    return text

def add_padding(text, padding, line_width):
    """
    Given a padding (between 0 and 1), this function appends whitespace
    roughly corresponding to that percentage of `line_width`.
    """
    num_spaces = int( padding * line_width )
    if (num_spaces == 0) and (padding != 0):
        num_spaces = 1

    padded_text = []
    for line in text:
        padded_text.append(num_spaces*' ' + line)

    return padded_text

def add_alignment_spacing(text, align_right, line_width):
    """
    If `align_right` is true, appends whitespace until the end of the line is
    comensurate with `line_width`.
    """
    if not align_right:
        return text

    right_aligned_text = []
    for line in text:
        num_spaces = line_width - len(line)
        right_aligned_text.append(num_spaces*' ' + line)

    return right_aligned_text

def parse_browser_poem_info(driver, line_width):
    """
    Given a webdriver `driver` THAT IS ALREADY NAVIGATED TO THE POEM WEBPAGE, 
    this method retrieves relevant info from the webpage, including the title,
    authors, and preface (e.g. "Translated from..." or other relevant quotes 
    before the poem text) as plain text.
    `line_width` is necessary for formatting the title and preface_lines
    appropriately.

    Parameters
    ----------
    driver : Selenium webdriver
        Webdriver that is already navigated to the poem url via driver.get(url).
    line_width : int
        Width of page where text will be printed, in number of characters

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
    title = delete_unprintable_characters(header.find_element(By.CLASS_NAME, 'type-gamma').text)
    title = textwrap.wrap(title, 
                          replace_whitespace=True, 
                          width=line_width)
    title = '\n'.join(title)
    authors = header.find_elements(By.CLASS_NAME, 'type-kappa')

    author_text = [delete_unprintable_characters(author.text) for author in authors]

    try:
        preface = main_content.find_element(By.CLASS_NAME, 'type-paragraph-sm').text
        preface = delete_unprintable_characters(preface)
        preface_lines = [line for line in preface.split('\n')]
        for i,_ in enumerate(preface_lines):
            preface_lines[i] = textwrap.wrap(preface_lines[i], 
                                             replace_whitespace=True, 
                                             width=line_width - 4)

            # if multiple lines, only get rid of one -- preserves poem formatting
            for line in preface_lines[i]:
                if check_for_leading_space(line):
                    line = line[1:]

            # add two spaces to show that it was originally one line
            n_leading_spaces = 2
            for j, _ in enumerate(preface_lines[i]):
                if j == 0:
                    continue
                else:
                    preface_lines[i][j] = n_leading_spaces*' ' + preface_lines[i][j]

    except NoSuchElementException:
        preface_lines = None

    original_window = driver.current_window_handle
    image_links = []
    try:
        author_links = [author.find_element(By.TAG_NAME, 'a').get_attribute('href') for author in authors]
        for link in author_links:
            driver.switch_to.new_window('tab')
            driver.get(link)
            main_content = driver.find_element(By.ID, 'mainContent')
            author_image = main_content.find_element(By.TAG_NAME, 'img')
            image_links.append(author_image.get_attribute('src'))
        driver.close()
    except NoSuchElementException:
        driver.close()

    driver.switch_to.window(original_window)

    return title, author_text, preface_lines, image_links

def split_styles(style_text):
    """
    Splits inline styles of an HTML tag. 

    Parameters
    ----------
    style_text : string
        String of inline styles on HTML tag. 

    Returns
    -------
    styles : array of strings
        Array where each element is one of the inline styles of the HTML element

    An example HTML tag might have the form:
        <div style="text-indent: -1em; padding-left: 1em;">
    The `style_text` input would then be:
        "text-indent: -1em; padding-left: 1em;"
    and the `styles` output would be:
        ['text-indent:-1em', 'padding-left:1em']
    Note that whitespace and semi-colons are eliminated
    """
    styles = style_text.replace(' ', '').split(';')
    styles.remove('')
    return styles

def strip_html(text):
    """
    Newlines and `<br>` tags happen to be superfluous in the poems.
    `&amp;` and `&nbsp` get converted to regular characters.
    `<i></i>` converted to `<em></em>` for bolding consistency.

    Parameters
    ----------
    text : string
        Inner HTML of tag representing line of a poem

    Returns
    -------
    text : string
        Line of a poem with all HTML removed except <em> tags.
    """
    text = re.sub('\n ', '', text)
    text = re.sub('<br>', '', text)
    text = re.sub('&amp;', '&', text)
    text = re.sub('&nbsp;', ' ', text)
    text = re.sub('<i>', '<em>', text)
    text = re.sub('</i>', '</em>', text)

    return text

def get_em_word_indices(text):
    """
    Return word indices of start and end of each block of text surrounded by
    <em> tags.

    Returns text with `<em>` tags removed, and also returns a list of
    2-tuples, where each tuple corresponds to a bolded span of text, the
    first number in the tuple is the zero-based index of the word where the 
    bold starts, and the second is one more than where the bold ends.
    Hence, if `idx` is an element of `em_indices` then. 

    Examples
    --------
    >>> text = 'Here <em>is some</em> example <em>bold text</em>.'
    >>> indices = get_em_word_indices(text)
    >>> indices
    [(1, 3), (3, 5)]

    >>> strip_text = re.sub('</?em>', '', text)
    >>> word_split = strip_text.split(' ')
    >>> for index in indices:
    >>>     start = index[0]
    >>>     end = index[1]
    >>>     print(word_split[start:end])
    ['is', 'some']
    ['bold', 'text']
    """
    splits = re.split('</?em>', text)
    for i,_ in enumerate(splits):
        splits[i] = re.sub(r'[\.,]', '', splits[i])

    em_word_indices = []
    word_count = len(splits[0].split())
    for i in range(1, len(splits), 2):
        bold_length = len(splits[i].split())
        non_bold_length = len(splits[i + 1].split())

        em_word_indices.append( (word_count, bold_length + word_count) )

        word_count += bold_length + non_bold_length

    return em_word_indices


def get_em_indices(em_text):
    splits = re.split('</?em>', em_text)

    indices = []
    char_count = len(splits[0])
    for i in range(1, len(splits), 2):
        start_idx = char_count
        end_idx = char_count + len(splits[i])
        indices.append( [start_idx, end_idx] )

        char_count = end_idx + len(splits[i + 1])

    text = ''.join(splits)

    return indices, text


def check_for_leading_space(string):
    return True if re.match(r'^\s', string) else False

def check_for_leading_triple_space(string):
    return True if re.match(r'^ {3}', string) else False

def delete_trailing_spaces(string):
    return re.sub(r'\s+$', '', string)

def wrap_text(wrapper, text, em_indices):
    """
    Wraps text so that it fits within a certain column-width, as dictated by
    the `wrapper` object.
    Also adds back in `<em>` tags according to `em_indices`.
    """
    wrapped_text = wrapper.wrap(text)

    line_indices = []
    cur_index = 0
    for line in wrapped_text:
        line_indices.append(cur_index)
        cur_index += len(line)
    
    i = 0
    index_offset = 0
    cur_line_index = 0
    for j, _ in enumerate(em_indices):
        while True:
            if em_indices[j][0] < cur_line_index + len(wrapped_text[i]):
                em_indices[j][0] += index_offset
                break
            cur_line_index += len(wrapped_text[i])
            i += 1
            index_offset += 2

        while True:
            if em_indices[j][1] < cur_line_index + len(wrapped_text[i]):
                em_indices[j][1] += index_offset
                break
            cur_line_index += len(wrapped_text[i])
            i += 1
            index_offset += 2



    # add <em> tags bag into text lines
    i = len(wrapped_text) - 1
    for index in reversed(em_indices):
        while True:
            if index[1] < line_indices[i]:
                i -= 1
                continue
            line = wrapped_text[i]
            idx = index[1] - line_indices[i]
            wrapped_text[i] = line[:idx] + '</em>' + line[idx:]
            break

        while True:
            if index[0] < line_indices[i]:
                i -= 1
                continue
            line = wrapped_text[i]
            idx = index[0] - line_indices[i]
            wrapped_text[i] = line[:idx] + '<em>' + line[idx:]
            break


    return wrapped_text


def parse_browser_poem_text(driver, line_width):
    """
    Given a webdriver `driver` THAT IS ALREADY NAVIGATED TO THE POEM WEBPAGE, 
    this method retrieves the lines of the poem in plain text, including
    limited formatting (like indenting or justification). 
    The character indexes at which `<em>` tags are found is also returned
    in the return object.
    The calling code can then use this to format text.

    Parameters
    ----------
    driver : Selenium webdriver
        Webdriver which is already navigated to the poem page via driver.get(url).

    Returns
    -------
    text_lines : array of TextLine objects
        Lines of the poem, already formatted with extra whitespace.
        Also included are character indices of `<em>` tags.

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
    wrapper = textwrap.TextWrapper(expand_tabs=False,
                                   subsequent_indent=2*' ',
                                   replace_whitespace=False, 
                                   drop_whitespace=False,
                                   width=line_width)
    for line in poem_lines:
        # cuts off last ';', splits by '; ' to get pure styles
        styles = split_styles( line.get_attribute('style') )
        text = line.get_attribute('innerHTML')

        try:
            span = line.find_element(By.XPATH, 'span')
            styles += split_styles( span.get_attribute('style') )
            text = span.get_attribute('innerHTML')
        except NoSuchElementException:
            pass

        try:
            div = line.find_element(By.XPATH, 'div')
            styles += split_styles( div.get_attribute('style') )
            text = div.get_attribute('innerHTML')
        except NoSuchElementException:
            pass

        align_right = 'text-align:right' in styles
        padding = 0
        for style in styles:
            padding_match = re.match(r'padding-left:(\d+)%', style)
            if not padding_match:
                continue
            padding = float(padding_match.group(1)) / 100

        text = strip_html(text)
        text = text.replace('\t', 4*' ')
        text = delete_unprintable_characters(text)

        em_indices, text = get_em_indices(text)

        text = wrap_text(wrapper, text, em_indices)

        # if triple spaces, only get rid of one -- preserves poem formatting
        # two spaces indent from textwrap, plus one leftover from between words
        for i,_ in enumerate(text):
            if check_for_leading_triple_space(text[i]):
                text[i] = text[i][1:]
            text[i] = delete_trailing_spaces(text[i])
        
        text = add_padding(text, padding, line_width)
        text = add_alignment_spacing(text, align_right, line_width)
        
        # Get poem lines as single string again
        text = '\n'.join(text)

        em_indices, text = get_em_indices(text)

        text_lines.append(TextLine(text, em_indices))


    return text_lines
