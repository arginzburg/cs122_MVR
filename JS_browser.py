# CS122 Project
#
# Vishok Srikanth / MVR
# 
# Python class to browse pages and perform searches where it's needed to 
# click elements on the page that result in complicated POST and GET requests
# that requests and similar packages won't handle properly.

# How to Set Up Linux Prerequisites on VMs:
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
import glob
import time
import signal
import subprocess
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException, StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pyvirtualdisplay import Display
from check_os import is_VM


class JS_browser:

    def __init__(self, save_path, invisible = True, start_link = False,
        download_wait = 600, verbose = False):
        '''
        Open a web browser, optionally navigating to a page. This browser can
        be used to click on elements within the page, which is particularly
        useful for clicking download links or check boxes and then taking some
        actions afterwards.
        Must include valid folder in "save_path" to specify where the downloads
        will go, preferably one that's empty before this class is used to do
        anything.
        '''
        self._invisible = invisible
        self._verbose = verbose
        self._download_wait = self._validate_time(download_wait, 600)
        self._save_path = save_path

        if self._invisible:
            self._display = Display(visible = 0, size = (800, 600))
            self._display.start()
        
        # Set the default download directory, since we can't rely on a dialog
        # box to control the location to which files download.
        #
        # http://stackoverflow.com/questions/36982639/changing-default-download-location-in-chrome-using-python-selenium
        chrome_options = webdriver.ChromeOptions()
        prefs = {"download.default_directory" : self._save_path}
        chrome_options.add_experimental_option("prefs", prefs)
        if is_VM():
            chromedriver = "/usr/bin/chromedriver "
        else:
            chromedriver = "/usr/local/bin/chromedriver"
        self._driver = webdriver.Chrome(executable_path = chromedriver, chrome_options = chrome_options)
        
        # Selenium functionality to a number of seconds for page elements to
        # appear if not immediately present when a function looks for them.
        self._driver.implicitly_wait(10)
        
        if start_link:
            self.go_to(start_link)


    def _validate_time(self, user_input, default):
        '''
        Check that a user input to be used as a download timeout has a valid
        (numeric) value or is "False".
        '''
        if user_input is False:
            return user_input
        if user_input is None:
            return default
        if not isinstance(user_input, (int, float)) or user_input < 0:
            if self._verbose:
                print("Error: Invalid wait time or timeout specification. "
                      "Input must be a non-negative number. \n Reverting "
                      "to default specification.")
            return default
        else:
            return user_input


    def go_to(self, link):
        '''
        Within the browser, navigate to the webpage at "link" and allow a delay
        time for the page's JavaScript elements to load.
        '''
        try:
            self._driver.get(link)
            self.wait_for_page_to_load()
            if self._verbose:
                print("Loaded new page successfully.")
        except WebDriverException:
            if self._verbose:
                print("Loading page failed. Check link is valid.")
 

    def wait_for_page_to_load(self):
        '''
        Checks for an element on the page that indicates some JavaScript
        element is loading, which means other desired actions should wait.
        '''
        loading_icon_path = '//img[@class="dxlp-loadingImage dxlp-imgPosLeft"]'
        # Note that this says "find_elements", not "find_element"
        loading_icons = self._driver.find_elements_by_xpath(loading_icon_path)
        not_loaded = True
        while not_loaded:
            try:
                while any([icon.is_displayed() for icon in loading_icons]):
                    time.sleep(1)
                not_loaded = False
            except StaleElementReferenceException:
                # Occasionally there are issues if these references haven't
                # been updated.
                loading_icons = self._driver.find_elements_by_xpath(loading_icon_path)


    def wait_for_clickable(self, element):
        '''
        Waits up to a minute for an element on a page to become clickable, if
        it is not already (e.g., if a "next page" button isn't clickable while
        the page is loading something.)

        Based on:
        http://stackoverflow.com/questions/28110008/python-selenium-wait-until-element-is-clickable-not-working
        '''
        wait_element = WebDriverWait(self._driver, 60).until(
                            EC.element_to_be_clickable((By.XPATH, element)))


    def element_exists(self, element):
        '''
        Returns True if an element exists on current page at given XPath, False
        otherwise. Similar to _find, but returns True/False instead of the
        element itself.
        '''
        try:
            self._driver.find_element_by_xpath(element)
            return True
        except NoSuchElementException:
            return False


    def click(self, element):
        '''
        Within the browser, click an element and allow some time for the page
        to respond. Specify the element to be clicked via XPath.
        '''
        button = self._find(element)
        if button:
            button.click()
            self.wait_for_page_to_load()


    def enter_text(self, element, text):
        '''
        Within the browser, populate the text field indicated by "element" with
        the value of "text".
        '''
        field = self._find(element)
        if field:
            field.click()   # Note this is not the JS_browser click method
            field.clear()   # Remove any pre-existing text from field
            field.send_keys(text)
        

    def _find(self, element):
        '''
        Retrieve a variable pointing to an element, if it exists on the current
        page.
        '''
        try:
            button = self._driver.find_element_by_xpath(element)
            return button
        except NoSuchElementException:
            return None


    def download(self, element, default_save_path, output_path = None,
        force_dowload_wait = None, is_simple = True, ext = None):
        '''
        Within the browser, click a download link to download some file,
        preventing user input until the download is complete. Optionally
        attempt to move the completed download file to a location specified
        by the user. "default_save_path" is the filepath the browser downloads
        to based on the value of "save_path" when constructing the browser
        instance and the procedure the webpage uses for generating a download
        file name (this has to be empirically determined). By default this is
        set to timeout downloads after 10 minutes, which can help avoid
        infinite loops caused by mistyping file paths.

        "is_simple" == False and "ext" != None should be used when a web page
        includes unpredictable strings in the file names for downloads; in such
        cases default_save_path should be the predictable prefix for this file
        name and ext should be the extension of the file type to be downloaded.
        '''
        if os.path.exists(default_save_path):
            # Default save path occupied. foo.txt will be downloaded as
            # foo(1).txt, etc. depending on how many similarly-named files are
            # in the default download location; we need to know to look for
            # the file where it will end up.
            try_name = default_save_path.replace(".", "({}).")
            i = 1
            while os.path.exists(try_name.format(i)):
                i += 1
            default_save_path = try_name

        if force_dowload_wait:
            max_time = self._validate_time(force_dowload_wait,
                                            self._dowload_wait)
        else:
            max_time = self._download_wait

        # By now, max_time is either something numeric or "False".
        if max_time:
            self.click(element)
            updated_path = self._timed_download(default_save_path, max_time,
                                                is_simple, ext)
        else:
            self.click(element)
            updated_path = self._download(default_save_path, is_simple, ext)

        if updated_path:
            default_save_path = updated_path
        if output_path:
            bash_command = ("mv " + r"\ ".join(default_save_path.split()) +
                            " " + output_path)
            # If there's an issue with the specified output path, an error
            # gets printed to the terminal automatically.
            subprocess.Popen(bash_command, shell = True)
        return None


    class TimeExceededException(Exception):
            '''
            A simple error class to handle optional time-outs (see below).
            '''
            pass


    def _timed_download(self, filepath, time_allowed, is_simple = True,
        ext = None):
        '''
        Check if a download has successfully completed, enforcing a time-out.
        '''
        # Based on suggestions from 
        # http://stackoverflow.com/questions/492519/timeout-on-a-function-call
        def handler(signum, frame):
            raise JS_browser.TimeExceededException
        timeout_handler = signal.signal(signal.SIGALRM, handler)
        try:
            alarm = signal.alarm(time_allowed)
            updated_path = self._download(filepath, is_simple, ext)
            alarm = signal.alarm(0)
            return updated_path
        except JS_browser.TimeExceededException:
            if self._verbose:
                print("Download Failed: Maximum download time exceeded.\n"
                      "If this is unexpected, ensure file paths were entered "
                      "properly.")
            return None


    def _download(self, filepath, is_simple = True, ext = None):
        '''
        Check if a download has successfully completed. This WILL hang if the
        file is specified improperly.
        '''
        if is_simple:
            while not os.path.exists(filepath):
                time.sleep(1)
                if self._verbose:
                    print("\n Waiting for download to finish at {}".format(
                            filepath))
            return None
        else:
            # is_simple = False is used when the web interface inserts
            # character strings into the the filename, such that the downloaded
            # file's name is unpredictable. This solution is based on
            # http://stackoverflow.com/questions/4296138/use-wildcard-with-os-path-isfile
            list_of_possible_dl_files = glob.glob(filepath + '*' + ext)
            if len(list_of_possible_dl_files) > 1:
                raise RuntimeError(
                      "\n User indicated download file name is not completely "
                      "predictable, as when random strings are included.\n"
                      "This option will ONLY work properly if there are no "
                      "files in the default download directory that have the "
                      "same extension as the one you are downloading. Be very "
                      "careful when using this option. \n")
            while len(list_of_possible_dl_files) < 1:
                # periodically check for the presence of the completed download
                time.sleep(1)
                if self._verbose:
                    print("\n Waiting for download to finish at {}".format(
                            filepath))
                list_of_possible_dl_files = glob.glob(filepath + '*' + ext)
            return list_of_possible_dl_files[0]


    def cleanup(self):
        '''
        Close the browser (and stop the virtual display, if the browser is
        running hidden).
        '''
        self._driver.quit()
        if self._invisible:
            self._display.stop()
        return None


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
        absolute filepaths. Useful for troubleshooting headless browsers.
        '''
        valid = self._driver.save_screenshot(directory + "/" + output_filename)
        if self._verbose and valid:
            print("Saved screenshot successfully.")
        elif self._verbose:
            print("Error saving screenshot.")
