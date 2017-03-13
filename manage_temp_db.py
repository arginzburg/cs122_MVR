# CS122 Project
#
# Vishok Srikanth / MVR
# 
# Code to take searches from NSF and TAGG and cache them temporarily

# Expects searches as a dictionary with the keys : value data types as follows
    # years : list of strings, empty if nothing selected
    # US_awards : True/False
    # keywords : a string of what the user searched, or the empty string
    # agency : ["NSF", "CDC", "NIH"] zero or more of these strings

# This database will hold the results of the last 20 searches, up to a maximum
# of 1,000 awards per search.

import os
import time
import subprocess
import sqlite3
from check_os import is_VM
from JS_browser import JS_browser
from collect_TAGG import setup_database
from populate_TAGG_search import search as TAGG_search
from nsf_scrape_search_result import run_search_scraper


def get_counts_for_search(search):
    '''
    Returns the number of grants from the NSF and TAGG search pages matching
    a particular search. Useful for implementing a warning that a user search
    is not specific enough and thus generates too many results to cache.

    Unfortunately the processes of performing searches and the functions set up
    to do them aren't really set up to just grab a value from the search result
    page and do nothing else: in some cases these functions already have so
    many parameters that adding another to conditionally elicit this behavior
    seems inadvisable, and it's easier to just reproduct the bits of those
    functions that do what we want here.

    Returns counts in the format (nsf, taggs, total)... if any of these
    exceed 1000, "OVER" is returned in that position instead.
    '''
    cache_name, temp_name, download_path = generate_file_paths()
    nsf_count, taggs_count = 0, 0
    if "NSF" in search["agency"]:
        url = generate_nsf_GET(search)
        num_result_element = '//div[@class="my-paging-display x-component"]'
        browser = JS_browser(download_path, start_link = url)
        # See explanation in download_nsf_search in this file.
        nsf_count = int(browser._find(num_result_element).text.split()[-1])
        print(nsf_count)
        browser.cleanup()
    if "CDC" in search["agency"] or "NIH" in search["agency"]:
        sub_search = search.copy()
        sub_search["agency"] = [value for value in search["agency"] if 
                                value != "NSF"]
        # The value of "download_path" here is irrelevant since we won't
        # download anything; it's just good to use a valid path.
        browser = JS_browser(save_path = "/")
        browser.go_to("https://taggs.hhs.gov/SearchAdv")
        years = search["years"]
        agency = sub_search["agency"]
        usa = search["US_awards"]
        intl = not usa
        keywords = search["keywords"]
        TAGG_search(browser, years = years, agency = agency, usa = usa,
                    intl = intl, keywords = keywords)
        award_count_elem = ('//div[.//text()="Distinct Award Count: "]/'
                            'following-sibling::div')
        taggs_count = int(browser._find(award_count_elem).text)
        print(taggs_count)
        browser.cleanup()
    
    total_count = nsf_count + taggs_count
    for count in [nsf_count, taggs_count, total_count]:
        if count >= 1000:
            count = "OVER"
    return nsf_count, taggs_count, total_count


def execute_search(search):
    '''
    Gets grants from the NSF and CDC and puts them in the database. Returns
    the count of NSF and TAGGS records found, along with the counter
    corresponding to the search just inserted into the temporary database.
    '''
    cache_name, temp_name, download_path = generate_file_paths()
    if not os.path.isfile(cache_name):
        initialize_db(cache_name)
    if not os.path.isfile(temp_name):
        initialize_db(temp_name)

    if "NSF" in search["agency"]:
        url = generate_nsf_GET(search)
        nsf_count, nsf_path = download_nsf_search(url, download_path)
        run_search_scraper(nsf_path, temp_name)
        subprocess.Popen("rm {}".format(nsf_path), shell = True)
    if "CDC" in search["agency"] or "NIH" in search["agency"]:
        sub_search = search.copy()
        sub_search["agency"] = [value for value in search["agency"] if 
                                value != "NSF"]
        # This function handles deleting the download inherently after data
        # has been added to the database.
        taggs_count = get_TAGGS(sub_search)
    # So far, the awards have been entered into a temporary database with the
    # same format as the real cached database. However, these new entries have
    # nothing in the "record_counter" table, though it should exist.
    temp_conn = sqlite3.connect(temp_name)
    temp_cursor = temp_conn.cursor()
    cache_conn = sqlite3.connect(cache_name)
    cache_cursor = cache_conn.cursor()
    # Fill out the counter and copy rows in "temp" to "cache"    
    counter = check_counter(cache_cursor)
    add_new_rows(temp_cursor, counter, cache_name)
    temp_conn.close()
    subprocess.Popen("rm {}".format(temp_name), shell = True)

    clean_old_rows(cache_cursor, counter)
    cache_conn.commit()
    cache_conn.close()

    return int(nsf_count), int(taggs_count), counter      


def generate_file_paths():
    '''
    Gets filepaths for cached search database and temporary storage for
    downloaded files based on system on which function is run.
    '''
    if is_VM():
        temp_name = "home/student/cs122_MVR/data/temp/temp.db"
        cache_name = "home/student/cs122_MVR/cached.db"
        download_path = "home/student/cs122_MVR/data/temp/"
    else:
        temp_name = "/Users/Vishok/Desktop/122/Assignments/Project/data/temp/temp.db"
        cache_name = "/Users/Vishok/Desktop/122/Assignments/Project/cached.db"
        download_path = "/Users/Vishok/Desktop/122/Assignments/Project/data/temp/"
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    return (cache_name, temp_name, download_path)


def initialize_db(db_filename):
    '''
    See notes below and in collect_TAGG.py about how much this function is my
    work (it's called "connect_db" there and does something very slightly
    different). Here I've copied it rather than importing because I needed to
    add the "counter" to each table. This has to be in each table, since we 
    need to distinguish between cached copies of records that resulted from 
    different searches.

    Initialize the cached award database, which has the following tables:
        awards, investigators, institutions, organizations, record_counter
    See sqlite3 commands below to see how these tables are linked.

    Mostly copied from MS's work in scrape_nsf.py. Can't import it because at
    time of writing this, that script contains code at the end outside any
    function or loop that I don't want to run when this script gets used.
    '''
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute('''CREATE TABLE awards
                (award_id text,
                 agency text,
                 title text,
                 abstract text,
                 amount int,
                 start_date char(10),
                 end_date char(10),
                 counter int,
                 constraint pk_awards primary key (award_id));''')
    c.execute('''CREATE TABLE investigators
                 (award_id text,
                  last_name text,
                  first_name text,
                  role text,
                  email text,
                  counter int,
                  constraint fk_investigators foreign key (award_id)
                  references awards (award_id));''')
    c.execute('''CREATE TABLE institutions
                 (award_id text,
                  name text,
                  address text,
                  city text,
                  state char(2),
                  zipcode text,
                  country text,
                  counter int,
                  constraint fk_institutions foreign key (award_id)
                  references awards (award_id));''')
    c.execute('''CREATE TABLE organizations
                 (award_id text,
                  organization_code int,
                  directorate text,
                  division text,
                  counter int,
                  constraint fk_organizations foreign key (award_id)
                  references awards (award_id));''')
    conn.commit()
    conn.close()
    # In this file, subsequent commands are built on other functions that
    # were designed earlier to make their own connections to the database.
    # Resultantly, we don't need/want the database connection and cursor.
    return None


def generate_nsf_GET(search):
    '''
    Generates the correct URL to access the NSF Advanced Search reults via a 
    get method, based on the parameters in the "search" dictionary.
    '''
    base_url = ("https://www.nsf.gov/awardsearch/advancedSearchResult"
        "?PIId="
        "&PIFirstName="
        "&PILastName="
        "&PIOrganization="
        "&PIState="
        "&PIZip="
        "&PICountry={}"
        "&ProgOrganization="
        "&ProgEleCode="
        "&BooleanElement=All"
        "&ProgRefCode="
        "&BooleanRef=All"
        "&Program="
        "&ProgOfficer="
        "&Keyword={}"
        "&AwardNumberOperator="
        "&AwardAmount="
        "&AwardInstrument="
        "&ActiveAwards=true"
        "&ExpiredAwards=true"
        "&OriginalAwardDateOperator=Range"
        "&OriginalAwardDateFrom=01%2F01%2F{}"
        "&OriginalAwardDateTo=12%2F31%2F{}"
        "&StartDateOperator="
        "&ExpDateOperator=")
    
    year_list = search["years"]
    if year_list:
        year_list.sort()
        start_year = year_list[0]
        end_year = year_list[-1]
    else:
        start_year = {}
        end_year = {}

    if search["US_awards"]:
        country = "US"
    else:
        country = ""

    keywords = search["keywords"]
    if keywords:
        keywords = "+".join(keywords.split())

    return base_url.format(country, keywords, start_year, end_year)


def download_nsf_search(url, download_path):
    '''
    Download the XML data from an NSF search, returning the number of results
    and the path at which the XML file is stored.
    '''
    xml_download_element = '//a[@title="Export as XML"]'
    num_result_element = '//div[@class="my-paging-display x-component"]'
    # Award.xml is the file name given by the website. We needn't bother
    # renaming this file as we'll just delete it once we're done.
    browser = JS_browser(download_path, start_link = url)
    # I realize it's not quite ideal to call a hidden method like this,
    # but the code required to get the number of search results in the NSF data
    # is pretty specific and thus it doesn't really seem appropriate to make
    # a method within the JS_browser class specifically for that purpose.
    # The text of the element at XPath num_result_element will be like:
    # "Displaying 1 - 30 of 3000"
    # So num_results would become 3000 in this case.
    num_results = browser._find(num_result_element).text.split()[-1]
    download_path += "Awards.xml"
    browser.download(xml_download_element, download_path)
    browser.cleanup()
    return num_results, download_path


def get_TAGGS(search):
    years = search["years"]
    agency = search["agency"]
    usa = search["US_awards"]
    keywords = search["keywords"]
    return setup_database(years = years, verbose = False, temporary = True,
                            usa = usa, keywords = keywords, agency = agency)


def check_counter(cache_cursor):
    '''
    Gets the current value of the incrementing counter used to implement the
    cached results database's behavior of deleting old results
    '''
    last_insertion = cache_cursor.execute('''SELECT MAX(counter)
                                                FROM awards;''').fetchone()[0]
    if last_insertion:
        return last_insertion + 1 # Return the next value to use
    else:   # e.g., if we just created the cache_db
        return 0    


def add_new_rows(temp_cursor, counter, cache_name):
    '''
    Populates the "record_counter" table in the temp database, then attaches
    the temporary database to the main one and copies over the rows.
    '''
    awards = temp_cursor.execute('''SELECT DISTINCT award_id
                                    FROM awards;''').fetchall()
    num_awards = len(awards)
    table_list = ['awards', 'investigators', 'institutions', 'organizations']
    for award_id in awards:
        for table in table_list:
            temp_cursor.execute('''INSERT OR REPLACE INTO {}
                                    (counter) VALUES (?);'''.format(table),
                                    (counter,))
    # Attach the temporary database to the main one, and copy over values.
    # Based on:
    # http://stackoverflow.com/questions/8215686/python-bulk-select-then-insert-from-one-db-to-another
    temp_cursor.execute('ATTACH "{}" AS cache'.format(cache_name))
    for table in table_list:
        temp_cursor.execute('''INSERT INTO cache.{}
                                SELECT * FROM {};'''.format(table, table))
    return None


def clean_old_rows(cache_cursor, counter):
    '''
    Deletes rows from the cached results database that are greater than 20
    searches old.
    '''
    table_list = ['awards', 'investigators', 'institutions', 'organizations']
    cutoff = counter - 20

    for table in table_list:
        cache_cursor.execute('''DELETE FROM {} WHERE
                                counter < ?;'''.format(table), (cutoff,))


# A sample "search" dictionary that gives a reasonable number of results
# for quick testing and manual corroboration.
search = {"years" : ["2012"], "US_awards" : True,
            "keywords" : "HIV virus immunology",
            "agency" : ["NSF", "NIH", "CDC"]}
