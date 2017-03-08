# Vishok Srikanth

import os
import bs4
import sqlite3

# How to Set Up Linux Prerequisites:
    # install selenium, pyvirtualdisplay
        # sudo pip3 install selenium pyvirtualdisplay
    # install xvfb and chromium
        # sudo apt-get updtae
        # sudo apt-get install xvfb chromium-browser
    # install older version of chromedriver manually:
        # Linux:https://chromedriver.storage.googleapis.com/index.html?path=2.26/
        # Download and extract the appropriate archive somewhere.
        # Open a terminal wherever the executable is (or use its full filepath)
            # sudo mv chromedriver /usr/bin/chromedriver

from JS_browser import JS_browser

link_to_visit = "https://www.nsf.gov/awardsearch/advancedSearchResult?PIId&PIFirstName&PILastName&PIOrganization&PIState&PIZip&PICountry&ProgOrganization&ProgEleCode&BooleanElement=All&ProgRefCode&BooleanRef=All&Program&ProgOfficer&Keyword=retina%20connectomics&AwardNumberOperator&AwardAmount&AwardInstrument&ActiveAwards=true&OriginalAwardDateOperator&StartDateOperator&ExpDateOperator"
xml_download_element = '//*[@id="x-auto-32"]/a'
default_save_path = "/home/student/Downloads/Awards.xml"
output_path = "/home/student/cs122_MVR/Awards.xml"

browser = JS_browser(start_link = link_to_visit)
browser.download(xml_download_element, default_save_path, output_path)
browser.cleanup()