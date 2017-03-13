# CS122 Project
#
# Vishok Srikanth / MVR
# 
# Python functions to interact with the DHHS's TAGG Advanced Search page to
# either construct the initial database or perform smaller searches to be
# cached in temporary additions to the database based upon user searches.
# 

import bs4
import re
import requests
import time
import pandas as pd
import subprocess
import sys
import os
import sqlite3
from populate_TAGG_search import search
from JS_browser import JS_browser
from selenium.common.exceptions import WebDriverException
from check_os import is_VM

def process_results(browser, default_save_path, output_path = None,
    download_element = "", is_simple = False, ext = ".csv",
    check_count = False, verbose = False):
    '''
    Walks through the pages of a TAGGS Advanced Search result, and:
        (0) Optionally, checks that the number of rows returned is under the
            maximum exportable limit
        (1) Downloads the CSV containing search results not including abstracts
        (2) Makes a list of the links to all Award Detail pages for Awards
            returned
        (3) Cleans up the JS_browser object
        (4) Visits each of the Award Detail pages and extracts an abstract
        (5) Returns a dictionary mapping Award Number : Abstract, which can be
            added to the downloaded data relatively easily

    "browser" should be a JS_browser navigated to the search result page.
    Default options for keyword arguments are set to make this succinct, since
    this is really the only use of this function for this project; they are
    made options so that in theory it would be easier to generalize this.

    "default_save_path", "is_simple", and "ext" are utilized as in the download
    method for the JS_browser class

    "check_count" prints a warning if 10,000 rows were exported, since this is
    the maximum value and suggests that some rows were probably excluded
    '''
    browser.download(download_element, default_save_path, output_path,
                        is_simple = is_simple, ext = ext)

    award_links = award_links_from_search(browser, verbose = verbose)
    # Close the JS_browser, which is no longer needed.
    browser.cleanup()
    collect_abstracts(award_links)

    if not output_path:
        print("\nDidn't relocate downloaded file to known location, unable to "
                "add abstract data to it. Returning dictionary mapping "
                "award number : abstract.\n")
        return award_links

    abstracts_to_df = {}
    abstracts_to_df['Award Number'] = [key for key in award_links]
    abstracts_to_df['Abstract'] = [text for text in award_links.values()]
    abstracts = pd.DataFrame(abstracts_to_df)

    grants = pd.read_csv(output_path, encoding ='latin1')
    if check_count and verbose and len(grants.index) == 10000:
        # Print a warning if the number of results exceeds 10,000, the maximum
        # number or results which can be downloaded. This is fine if we are 
        # using a search to expand the temporary database, in which case there
        # should be a cap on the number of rows added. 
        print("WARNING: Returned > 10,000 results for this search.")
    grants = grants.merge(abstracts, on = "Award Number")
    return grants


def award_links_from_search(browser, base_url = "https://taggs.hhs.gov",
    verbose = False):
    '''
    Locates and extracts the HTML links for Award Detail pages from all results
    pages from a TAGGS Advanced Search.

    "base_url" is left as an option for potential other applications, but the
    default option is sufficient for our use here. This value was determined
    empirically; since we're not using a requests library to walk through the 
    search results, we just have to find out what the base URL is for all the
    Award Detail pages, compared to how they are listed on the results page.
    '''
    next_page_button = '''//a[@onclick="ASPx.GVPagerOnClick('GridView','PBN');"]'''
    next_page_img = '//img[@alt="Go to next page"]'
    invalid_next_page_img = '//img[@alt="Go to next page - Link Disabled"]'
    # This flag is useful because the next/back buttons don't appear if the
    # search results fit on a single page.
    multiple_pages = False  
    # Get links from Page 1.
    award_links = award_links_from_page(browser, base_url, verbose)
    # Check if "next page" button is avaialable
    while browser.element_exists(next_page_img):
        multiple_pages = True
        browser.wait_for_clickable(next_page_button)
        # This is clearly a hack, for which I am sorry, but somehow despite
        # the preceding line I continue to get errors saying this element
        # isn't clickable. The solution seems to be to wait a while.
        while True:
            try:
                browser.click(next_page_button)
                break
            except WebDriverException:
                pass
        # Wait while the next page loads.
        browser.wait_for_page_to_load()
        page_award_links = award_links_from_page(browser, base_url, verbose)
        # Collapse the two dictionaries, preferring entries from the 
        # second - though it shouldn't matter for our usage.
        award_links.update(page_award_links)
    # Sanity check: if there don't appear to be further pages, the next page
    # button should now be invalid.
    if (verbose and
        multiple_pages and
        not browser.element_exists(invalid_next_page_img)):
        print("\n WARNING: Thought we reached last page of search results, "
                "but next page button ambiguous. Try increasing loading "
                "time allowance.")
    if verbose:
        print("Found {} distinct award links.".format(len(award_links)))
    return award_links


def award_links_from_page(browser, base_url, verbose = False):
    '''
    Locates and extracts the HTML links for Award Detail pages from a single
    TAGGS Advanced Search results page (these links are needed to collect full
    abstracts).
    '''
    award_links_on_page = {}
    
    result_soup = bs4.BeautifulSoup(browser.source, "lxml")
    # For the moment, these are actually anchors, not links, I am aware.
    # http://stackoverflow.com/questions/35465182/how-to-find-all-divs-whos-class-starts-with-a-string-in-beautifulsoup
    award_links = result_soup.find_all("a",
                                        class_ = "dxeHyperlink_newTAGGSTheme",
                                        href=re.compile("^/Detail/AwardDetail"))
    award_links = [anchor.get("href") for anchor in award_links]
    # Award Detail links have a general format of
    # "/Detail/AwardDetail?arg_AwardNum=B01DP009001&arg_ProgOfficeCode=120"
    # i.e., they contain the award number; we want to use this as the key
    # for our dictionary of award links.
    for link in award_links:
        link_search = re.search('(arg_AwardNum=)([A-Z0-9]+)(&arg)', link)
        # link_search == None if the RegEx failed somehow.
        if link_search:
            award_number = link_search.group(2)
            # Using a dictionary like this also eliminates duplicates, which
            # may arise from one or more renewals for a grant being returned
            # for the search (the original grant and its renewals share an
            # Award Detail page).
            award_links_on_page[award_number] = base_url + link
        else:
            print("\n had difficulty parsing link: \n\t{}".format(link))
    return award_links_on_page


def collect_abstracts(award_links):
    '''
    Iterates over the Award Number: Award Detail Link dictionary and replaces
    Award Detail links with the abstracts appearing on the linked page.
    '''
    for award_number in award_links:
        detail_html = requests.get(award_links[award_number]).content
        detail_soup = bs4.BeautifulSoup(detail_html, "lxml")
        text = detail_soup.find("div", id="AbstractRoundPanel_CRC").text
        text = text.replace("DESCRIPTION (provided by applicant):", "").strip()
        award_links[award_number] = text
    return None


def download_awards(years, download_path, default_save_path, output_path,
    start_page, download_element, output_files, name = None, temporary = False,
    states = [], usa = True, keywords = "", agency = [], verbose = False):
    '''
    For a given state abbreviation in "name", download the TAGGS data we need
    to set up the database corresponding to that state. If "name" == "INTL",
    download data for grants awarded outside the US instead.

    Returns the path of the file to which downloaded data was written.
    '''
    output = output_path.format(name)
    browser = JS_browser(download_path, invisible = False, verbose = verbose)
    browser.go_to(start_page)
    
    # "temporary" is a little superfluous since "name" is only used when 
    # "temporary" == False. However, I think including it makes this control
    # flow much clearer; hopefully that's deemed acceptable/good.
    if not temporary:
        if name != "INTL":
            # Detailed further in populate_TAGG_search.py, "search" function
            # performs a search within the JS_browser object, navigating the
            # browser to Page 1 of the results associated with the search as
            # constrained by inputs to "search".
            search(browser, years = years, states = [name], intl = False)
        else:
            search(browser, years = years, usa = False)
        
        award_df = process_results(browser, default_save_path, output,
                                    download_element, check_count = True,
                                    verbose = verbose)
        if verbose:
            print('Downloaded and stored files for grants in {}'.format(name))
        output_files.append(output)
        return award_df
    
    else:
        award_count_elem = ('//div[.//text()="Distinct Award Count: "]/'
                            'following-sibling::div')

        if usa:
            search(browser, years = years, states = states, intl = False,
                keywords = keywords, agency = agency)
        else:
            search(browser, years = years, states = [], usa = False,
                keywords = keywords, agency = agency)
        # I realize it's not quite ideal to call a hidden method like this,
        # but the code required to get the number of search results in the TAGG
        # data is pretty specific and thus it doesn't really seem appropriate
        # to make a method within the JS_browser class specifically for that
        # purpose. 
        award_count = browser._find(award_count_elem).text
        award_df = process_results(browser, default_save_path, output,
                                    download_element, verbose = verbose)
        return award_df, award_count



def add_TAGG_award(row, c):
    '''
    !!! Mostly not my work. I changed a few things, like parametrization,
    !!! because I needed to be able to input 'Null' values. - VS

    Take in a row from a pandas DataFrame which corresponds to an award, and
    inserts the data for this award into a SQL database for all TAGGS.

    "row" should have the following columns:
        'OPDIV', 'Recipient Name', 'Recipient Address' 'Recipient City',
        'Recipient State', 'Recipient ZIP Code', 'Recipient Country',
        'Award Number', 'Award Title', 'Action Issue Date',
        'CFDA Program Name', 'Principal Investigator', 'Sum of Actions ',
        'Abstract'

    "c" should be a cursor for the database to populate

    This is heavily based on MS's function add_award_to_db in nsf_scrape.py to
    make this database easily added to that one and vice versa.
    '''
    award_id = row['Award Number']
    agency = row['OPDIV']
    title = row['Award Title']
    abstract = row['Abstract']
    amount = int(row['Sum of Actions '].strip().
                    replace("$", "").replace(",", ""))
    # We're mostly interested in the grant awarding process, so the date the
    # grant was awarded is more important than the starting fiscal year.
    start_date = row['Action Issue Date']
    end_date = None # Information not available from TAGGS data
    c.execute('''INSERT OR REPLACE INTO awards (award_id, agency, title,
                abstract, amount, start_date, end_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (award_id, agency, title, abstract, amount, start_date,
                    end_date))

    name = row['Principal Investigator']
    if isinstance(name, str):
        name_parsed = name.split()
    else:
        name_parsed = None
    if name_parsed and len(name_parsed) > 1:
        # If only one name is listed, place it into the first and last name
        # fields since we can't easily tell which has been omitted or how to
        # categorize a single name if there has been no omission.
        first_name = " ".join(name_parsed[:-1])
        last_name = name_parsed[-1]
    else:
        first_name = None
        last_name = name
    email = None
    role = None
    c.execute('''INSERT OR REPLACE INTO investigators (award_id, last_name,
                first_name, role, email) VALUES (?, ?, ?, ?, ?)''',
                (award_id, last_name, first_name, role, email))

    name = row['Recipient Name']
    address = row['Recipient Address']
    city = row['Recipient City']
    state_code = row['Recipient State']
    zipcode = row['Recipient ZIP Code']
    country = row['Recipient Country']
    if country == "United States of America":
        country = "United States" # Enforce NSF's shorter listing for USA
    c.execute('''INSERT OR REPLACE INTO institutions (award_id, name, address,
                 city, state, zipcode, country)
                 VALUES (?, ?, ?, ?, ?, ?, ?)''',
                 (award_id, name, address, city, state_code, zipcode, country))

    organization_code = None
    directorate = None
    # Nearest approximation of appropriate data for this field.
    division = row['CFDA Program Name']
    c.execute('''INSERT OR REPLACE INTO organizations (award_id,
                 organization_code, directorate, division)
                 VALUES (?, ?, ?, ?)''',
                 (award_id, organization_code, directorate, division))


def store_awards(award_df, cursor, verbose = False):
    '''
    Simple helper function that implements the row-wise process of taking a
    dataframe of award data and placing it into the database structure.
    '''
    for index, row in award_df.iterrows():
        add_TAGG_award(row, cursor)
    if verbose:
        print('\tSuccessfully added this data to SQL database.')


def connect_db(db_filename):
    '''
    !!! Almost entirely not my work. I helped decide on this structure,
    !!! but wrote very little of this code. - VS

    Initialize the award database, which has the following tables:
        awards, investigators, institutions, and organizations
    See sqlite3 commands below to see how these tables are linked.

    Mostly copied from MS's work in scrape_nsf.py. Can't import it because at
    time of writing this, that script contains code at the end outside any
    function or loop that I don't want to run when this script gets used.
    '''
    create_new_tables = not os.path.isfile(db_filename)
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    if create_new_tables:
        c.execute('''CREATE TABLE awards
                    (award_id text,
                     agency text,
                     title text,
                     abstract text,
                     amount int,
                     start_date char(10),
                     end_date char(10),
                     constraint pk_awards primary key (award_id));''')
        c.execute('''CREATE TABLE investigators
                     (award_id text,
                      last_name text,
                      first_name text,
                      role text,
                      email text,
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
                      constraint fk_institutions foreign key (award_id)
                      references awards (award_id));''')
        c.execute('''CREATE TABLE organizations
                     (award_id text,
                      organization_code int,
                      directorate text,
                      division text,
                      constraint fk_organizations foreign key (award_id)
                      references awards (award_id));''')
    return (conn, c)


def setup_database(years = [], verbose = True, temporary = False, usa = True,
    keywords = "", agency = []):
    '''
    Sets up database of CDC and NIH grants. Runs if this script
    (collect_TAGG.py) is executed from the terminal. In this case "years"
    should have a single entry. Since the user isn't really going to interact
    with this function it's not so important to setup error messages that
    express this constraint and throw errors if it is violated.

    When temporary = True, the user has the option to preserve downloaded
    files. Other the data is input into the database, but associated downloads
    will automatically be deleted.

    Also setup to be usable with a more specific search by specifying
    temporary = TRUE and specifying values for "usa" an "keywords", which is
    helpful when we want to make a smaller search to input into a cached
    results database.
    '''
    start_page = "https://taggs.hhs.gov/SearchAdv"
    download_element = '//*[@id="btnExportToCSVSearchAdvExport_AdvSearchFilter"]'
    output_files = []
    states = ['AL', 'AK', 'AS', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FM', 
                'FL', 'GA', 'GU', 'HI', 'ID', 'IL', 'IN', 'IA', 'JQ', 'KS',
                'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT',
                'MQ', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'MP',
                'BQ', 'OH', 'OK', 'OR', 'PA', 'PR', 'MH', 'PW', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VI', 'VA', 'WA', 'WV', 'WI',
                'WY', 'WQ']
    
    # For setup of databases to be stored permanently.
    if not temporary:
        if is_VM():
            db_name = "home/student/cs122_MVR/taggs{}.db"
            download_path = "home/student/cs122_MVR/data/taggs{}/"
        else:
            db_name = "/Users/Vishok/Desktop/122/Assignments/Project/taggs{}.db"
            download_path = "/Users/Vishok/Desktop/122/Assignments/Project/data/taggs{}/"

        db_name = db_name.format("_" + years)
        download_path = download_path.format("/" + years)
        if not os.path.exists(download_path):
            os.makedirs(download_path)
        output_path = download_path + "TAGGS_{}.csv"
        default_save_path = download_path + "TAGGS Export "

        connection, cursor = connect_db(db_name)
        
        # Separately download/scrape and format data from each U.S. state.
        for state in states:
            award_df = download_awards(years, download_path,
                                        default_save_path, output_path,
                                        start_page, download_element,
                                        output_files, name = state,
                                        verbose = verbose)
            store_awards(award_df, cursor, verbose)
             # Save database in case of unexpected errors, e.g., web connection
             # loss.
            connection.commit()
        # Download/scrape and format data from grants awarded outside the US.
        # I chose not to wrap this code and the contents of the loop directly
        # above this because although there is a little bit of repeated code,
        # it's relatively easier to read and understand this way as opposed to
        # the alternative of storing many of these search parameters in some
        # secondary variable and passing that to some other function to call
        # download_awards and store_awards.
        award_df = download_awards(years, download_path,
                                    default_save_path, output_path, start_page,
                                    download_element, output_files,
                                    name = "INTL", verbose = verbose)
        store_awards(award_df, cursor, verbose)
        connection.commit() # Save database

        connection.close()  # Close database
        do_not_clean = input("\nDatabase download/construction complete. You "
                                "now may choose to keep the CSV files used to "
                                "create the database, or choose to remove "
                                "them. To preserve these files input any "
                                "non-empty string and press ENTER; to delete "
                                "them input the empty string and press ENTER."
                                "\n")
        if not do_not_clean:
            for source_file in output_files:
                bash_command = ("rm {}".format(source_file))
                subprocess.Popen(bash_command, shell = True)

        print("\nDatabase construction for TAGGS data complete!")
        return None
    
    # For input of data into temporary search result-caching database and the
    # setup thereof.
    else:
        if is_VM():
            db_name = "home/student/cs122_MVR/data/data/temp/temp.db"
            download_path = "home/student/cs122_MVR/data/temp/"
        else:
            db_name = "/Users/Vishok/Desktop/122/Assignments/Project/data/temp/temp.db"
            download_path = "/Users/Vishok/Desktop/122/Assignments/Project/data/temp/"

        output_path = download_path + "TAGGS_temp.csv"
        default_save_path = download_path + "TAGGS Export "

        # Create the temporary database if it exists, otherwise just open it.
        connection, cursor = connect_db(db_name)

        award_df, count = download_awards(years, download_path,
                                            default_save_path, output_path,
                                            start_page, download_element,
                                            output_files, temporary = True,
                                            states = states, usa = usa,
                                            keywords = keywords,
                                            agency = agency, verbose = False)
        store_awards(award_df, cursor, verbose)
        connection.commit() # Save database
        connection.close()  # Close database
        # Output_files should have length 1 when temporary = True, since only
        # a single search is performed.
        bash_command = ("rm {}".format(output_path))
        subprocess.Popen(bash_command, shell = True)
        return count


if __name__=="__main__":
    num_args = len(sys.argv)

    usage = ("usage: python3 " + sys.argv[0] + " <year>" +
            "\n Populates initial database of CDC and NIH grants. Year input "
            " must be a number between 1991 and 2017.")

    if num_args == 2:
        try:
            validate_input = (int(sys.argv[1]))
            # We need to check if this input is a valid year, but actually
            # want to use it as a string.
            setup_database(sys.argv[1])
        except ValueError:
            print(usage)
            sys.exit(0)
    else:
        print(usage)
        sys.exit(0)
