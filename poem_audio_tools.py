from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def get_audio_link(driver: webdriver.Firefox) -> str | None:
    """
    With driver already navigated to poem, this function returns a link to
    the audio file.

    If there is no audio associated with the poem, it returns None
    """
    main_content = driver.find_element(By.ID, 'mainContent')
    header = main_content.find_element(By.TAG_NAME, 'header')
    button = header.find_element(By.TAG_NAME, 'button')

    if button.text != 'Play Audio':
        return None

    button.click()
    time.sleep(2)
    audio = header.find_element(By.TAG_NAME, 'audio')
    audio_link = audio.get_attribute('src')

    return audio_link
