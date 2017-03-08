# Vishok Srikanth

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
output_path = "/media/sf_VM_Folder/Awards.xml"

browser = JS_browser(start_link = link_to_visit)
browser.download(xml_download_element, default_save_path, output_path)
browser.cleanup()

# import os
# import time
# import subprocess
# from selenium import webdriver
# from pyvirtualdisplay import Display

# link_to_visit = "https://www.nsf.gov/awardsearch/advancedSearchResult?PIId&PIFirstName&PILastName&PIOrganization&PIState&PIZip&PICountry&ProgOrganization&ProgEleCode&BooleanElement=All&ProgRefCode&BooleanRef=All&Program&ProgOfficer&Keyword=retina%20connectomics&AwardNumberOperator&AwardAmount&AwardInstrument&ActiveAwards=true&OriginalAwardDateOperator&StartDateOperator&ExpDateOperator"

# display = Display(visible=0, size=(800, 600))
# display.start()

# driver = webdriver.Chrome()
# driver.get(link_to_visit)
# # Wait long enough for the page to finish loading elements. Maybe change this
# # later to wait for some workpiece indicator to appear, but for now this works.
# # This is hackeneyed, but the page loads the download button before everything
# # else...
# time.sleep(10)
# # input("Please press Enter once the browser shows the page is finished downloading.")
# # Get the xpath manually by inspecting element in Chrome and right click ->
# # copy -> xpath
# download_link = driver.find_element_by_xpath('//*[@id="x-auto-30"]/a')
# # Downloads the file. The default directory is the "Downloads" directory,
# # I'm sure there's a way to control it but idk how yet. Anyway, at least it's
# # predictable.
# download_link.click()

# # Wait for the download to finish.
# # while not os.path exists("/Users/Vishok/Downloads/Awards.csv"):     # OS X
# while not os.path.exists("/home/student/Downloads/Awards.csv"):       # Linux
#     time.sleep(10)

# # Visible Browser Alternative
# # input("\nPlease press Enter once the browser shows the file is finished downloading.\n")

# # Clean Up.
# driver.quit()
# display.stop()

# filepath = input("\nPlease input a destination directory and name for the "
#                  "downloaded CSV file, (no quotation marks, spaces, etc. but "
#                  "including '.csv' if desired) or nothing if you wish to move "
#                  "it manually.\n")
# if filepath:
#     # bash_command = "mv /Users/Vishok/Downloads/Awards.csv " + filepath
#     bash_command = "mv /home/student/Downloads/Awards.csv " + filepath
#     subprocess.Popen(bash_command, shell = True)
