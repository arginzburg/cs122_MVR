# Vishok Srikanth
# 
# Python class to browse pages and perform searches where it's needed to 
# click elements on the page that result in complicated POST and GET requests
# that requests and similar packages won't handle properly.

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

import os
import time
import signal
import subprocess
from selenium import webdriver
from pyvirtualdisplay import Display

class JS_browser:

    def __init__(self, invisible = True, start_link = False, load_time = 10,
                 verbose = False):
        '''
        Open a webbrowser, navigating to a page. This browser can be used to
        click on elements within the page, which is particularly useful for
        clicking download links or check boxes and then taking some actions
        afterwards.
        '''
        self._invisible = invisible
        self._verbose = verbose
        self._load_time = load_time

        if self._invisible:
            self._display = Display(visible=0, size=(800, 600))
            self._display.start()
        self._driver = webdriver.Chrome()
        if start_link:
            self.go_to(start_link)

    @property
    def source(self):
        '''
        Return HTML source code of the browser's current page.
        '''
        return self._driver.page_source

    @property
    def capture(self, output_filename, directory = os.getcwd()):
        '''
        Screenshot the web browser, saving PNG to "output_filename".png in
        current directory unless alternative is specified. Only accepts
        absolute filepaths.
        '''
        valid = self._driver.save_screenshot(directory + "/" + output_filename)
        if self._verbose and valid:
            print("Saved screenshot successfully.")
        elif self._verbose:
            print("Error saving screenshot.")
   

    def go_to(self, link):
        '''
        Within the browser, navigate to the webpage at "link" and allow a delay
        time for the page to load.
        '''
        try:
            self._driver.get(link)
            time.sleep(self._load_time)
            if self._verbose:
                print("Loaded new page successfully.")
        except WebDriverException:
            if self._verbose:
                print("Loading page failed. Check link is valid.")
 

    def click(self, element):
        '''
        Within the browser, click an element and allow some time for the page
        to respond. Specify the element to be clicked via XPath.
        '''
        self._find_and_click(element)


    def _find_and_click(self, element):
        try:
            button = self._driver.find_element_by_xpath(element)
            button.click()
            time.sleep(self._load_time)
        except NoSuchElementException:
            if self._verbose:
                print("Couldn't locate element. Maybe increase loading time?")


    class TimeExceededError(Exception):
        '''
        A simple error class to handle optional time-outs (see below).
        '''
        pass


    def download(self, element, default_save_path, output_path = None,
                 max_time = 600):
        '''
        Within the browser, click a download link to download some file,
        preventing user input until the download is complete. Optionally
        attempt to move the completed download file to a location specified
        by the user. "default_save_path" is the filepath the browser downloads
        to by default (e.g., Chromium on the Linux VMs saves downloads to
        "/home/student/Downloads/" so if we wish to click a link that downloads
        a file called "Awards.xml" the default_save_path should be
        "/home/student/Downloads/Awards.xml"; unfortunately this has to be
        empirical). By default this is set to timeout downloads after 10
        minutes, which can help avoid infinite loops caused by mistyping file
        paths.
        '''
        # Default save path occupied. foo.txt will be downloaded as foo(1).txt,
        # etc. depending on how many similarly-named files are in the default
        # download location.
        if os.path.exists(default_save_path):
            try_name = default_save_path.replace(".", "({}).")
            i = 1
            while os.path.exists(try_name.format(i)):
                i += 1
            default_save_path = try_name

        if max_time:
            if not isinstance(max_time, (int, float)):
                if self._verbose:
                    print("Error: Invalid timeout specification. Must be a "
                          "number to be used as maximum allowable seconds to "
                          "try download process.")
            self._find_and_click(element)
            self._timeout_download(default_save_path, max_time)
        else:
            self._find_and_click(element)
            self._download(default_save_path)

        if output_path:
            bash_command = "mv " + default_save_path + " " + output_path
            # If there's an issue with the specified output path, an error
            # gets printed to the terminal automatically.
            subprocess.Popen(bash_command, shell = True)


    def _timeout_download(self, filepath, time_allowed):
        '''
        Check if a download has successfully completed, enforcing a time-o
        '''
        # Based on suggestions from 
        # http://stackoverflow.com/questions/492519/timeout-on-a-function-call
        def handler(signum, frame):
            raise TimeExceededError
        timeout_handler = signal.signal(signal.SIGALRM, handler)
        try:
            alarm = signal.alarm(time_allowed)
            self._download(filepath)
            alarm = signal.alarm(0)
        except TimeExceededError:
            if self._verbose:
                print("Download Failed: Maximum download time exceeded.\n"
                      "If this is unexpected, ensure file paths were entered "
                      "properly.")


    def _download(self, filepath):
        '''
        Check if a download has successfully completed. This WILL hang if the
        file is specified improperly.
        '''
        while not os.path.exists(filepath):
            time.sleep(10)


    def cleanup(self):
        '''
        Close the browser (and stop the virtual display, if the browser is
        running hidden).
        '''
        self._driver.quit()
        if self._invisible:
            self._display.stop()
