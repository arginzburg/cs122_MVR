# Functions to download NSF data using advanced search option from the NSF
# Website
#
# Vishok Srikanth, Mark Saddler
#

import os
import time
import subprocess
from selenium import webdriver
from pyvirtualdisplay import Display


def download_xml_file_from_search_url(search_url, output_xml_fn):
    '''
    By Vishok Srikanth
    '''
    display = Display(visible=0, size=(800, 600))
    display.start()
    
    driver = webdriver.Chrome()
    driver.get(search_url)
    # Wait long enough for the page to finish loading elements. Maybe change this
    # later to wait for some workpiece indicator to appear, but for now this works.
    # This is hackeneyed, but the page loads the download button before everything
    # else...
    time.sleep(10)
    # input("Please press Enter once the browser shows the page is finished downloading.")
    # Get the xpath manually by inspecting element in Chrome and right click ->
    # copy -> xpath
    download_link = driver.find_element_by_xpath('//*[@id="x-auto-32"]/a')
    # Downloads the file. The default directory is the "Downloads" directory,
    # I'm sure there's a way to control it but idk how yet. Anyway, at least it's
    # predictable.
    download_link.click()
    # Wait for the download to finish.
    # while not os.path exists("/Users/Vishok/Downloads/Awards.xml"):     # OS X
    while not os.path.exists("/home/student/Downloads/Awards.xml"):       # Linux
        print('downloading search results...')
        time.sleep(10)
    # Clean Up.
    driver.quit()
    display.stop()

    filepath = '/home/student/cs122_MVR/data/nsf_tmp/' + output_xml_fn
    bash_command = "mv /home/student/Downloads/Awards.xml " + filepath
    subprocess.Popen(bash_command, shell = True)





url = 'https://www.nsf.gov/awardsearch/advancedSearchResult?\
       PIId=&\
       PIFirstName=&\
       PILastName=&\
       PIOrganization=&\
       PIState=&\
       PIZip=&\
       PICountry=&\
       ProgOrganization=&\
       ProgEleCode=&\
       BooleanElement=All&\
       ProgRefCode=&\
       BooleanRef=All&\
       Program=&\
       ProgOfficer=&\
       Keyword=beaked+whale+acoustics&\
       AwardNumberOperator=&\
       AwardAmount=&\
       AwardInstrument=&\
       ExpiredAwards=true&\
       OriginalAwardDateOperator=Before&\
       OriginalAwardDateTo=12%2F31%2F2011&\
       StartDateOperator=&\
       ExpDateOperator='

out = 'test.xml'

download_xml_file_from_search_url(url, out)