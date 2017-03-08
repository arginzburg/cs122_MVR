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
from populate_TAGG_search import search
from JS_browser import JS_browser
from nsf_scrape import init_db


def process_results(browser, default_save_path, output_path = None,
    download_element = "", is_simple = False, ext = ".csv",
    check_count = False):
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

    "check_count" should rarely be used, see comments below.
    '''
    if check_count:
        # Print a warning if the number of results exceeds 10,000, the maximum
        # number or results which can be downloaded. This is fine if we are 
        # using a search to expand the temporary database, in which case there
        # should be a cap on the number of rows added.
        # This is sensitive to the inputs of the search, and thus shouldn't
        # really be used except when downloading the whole database (in which
        # case the search is known ahead of time).
        # 
        count_path =  '//*[@id="mp-pusher"]/div[3]/div/div[3]/div[2]/div[1]/div/div[10]'
        count_results = int(browser._find(count_path).text)
        if count_results > 10000:
            print("WARNING: Returned > 10,000 results for this search.")
    browser.download(download_element, default_save_path, output_path,
                        is_simple = is_simple, ext = ext)

    award_links = award_links_from_search(browser)
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

    grants = pd.read_csv(output_path)
    # The exporter appears to insert an empty column; remove it.
    grants = grants.drop('Unnamed: 2', axis = 1)
    grants = grants.merge(abstracts, on = "Award Number")
    # Overwrite the original downloaded file to add the abstracts to it.
    grants.to_csv(output_path, index = False)

    return None


def award_links_from_search(browser, base_url = "https://taggs.hhs.gov"):
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

    # Get links from Page 1.
    award_links = award_links_from_page(browser)
    # Check if "next page" button is avaialable
    while browser.element_exists(next_page_img):
        browser.click(next_page_button)
        time.sleep(10)
        page_award_links = award_links_from_page(browser)
        # Collapse the two dictionaries, preferring entries from the 
        # second - though it shouldn't matter for our usage.
        award_links = {**award_links, **page_award_links}
    # Sanity check: if there don't appear to be further pages, the next page
    # button should now be invalid.
    if not browser.element_exists(invalid_next_page_img):
        print("\n WARNING: Thought we reached last page of search results, "
                "but next page button ambiguous. Try increasing loading "
                "time allowance.")
    return award_links


def award_links_from_page(browser, base_url = "https://taggs.hhs.gov"):
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


def stitch_data(output_path, award_links):
    '''
    Adds abstract information to downloaded grant information.
    '''
    pass


def setup_database():
    '''
    If script is run with no arguments, sets up database of CDC and NIH grants.
    '''
    cursor, connection = init_db("home/student/cs122_MVR/taggs.db")

    states = ['AL', 'AK', 'AS', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FM', 
                'FL', 'GA', 'GU', 'HI', 'ID', 'IL', 'IN', 'IA', 'JQ', 'KS',
                'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT',
                'MQ', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'MP',
                'BQ', 'OH', 'OK', 'OR', 'PA', 'PR', 'MH', 'PW', 'RI', 'SC',
                'SD', 'TN', 'TX', 'UT', 'VT', 'VI', 'VA', 'WA', 'WV', 'WI',
                'WY', 'WQ']

    start_page = "https://taggs.hhs.gov/SearchAdv"
    csv_download_element = '//*[@id="btnExportToCSVSearchAdvExport_AdvSearchFilter"]'

    default_save_path = "/Users/Vishok/Downloads/TAGGS Export "
    output_path = "/Users/Vishok/Desktop/TAGGS_{}.csv"
    output_files = []
    # default_save_path = "/home/student/Downloads/TAGGS Export " #Linux
    # output_path = "home/student/cs122_MVR/data/taggs/TAGGS_{}.csv"

    # Separately download/scrape and format data from each U.S. state.
    for state in states:
        output = output_path.format(state) 
        
        browser = JS_browser(verbose = True, load_wait = 5)
        browser.go_to(start_page, force_load_wait = None)
        search(browser, states = [state], intl = False, keywords = "HIV")
        
        process_results(browser, default_save_path, output,
                        csv_download_element)
        output_files.append(output)

    # Download/scrape and format data from grants awarded outside the US.



def add_TAGG_award(award, c):
    '''
    Take in a dictionary (award), which contains all of the fields parsed from
    a single XML file, and insert all fields into the NSF database.
    '''
    award_id = int(award.get('awardid', None))
    title = award.get('awardtitle', '').\
            replace('\'', '').replace('\"', '')
    abstract = award.get('abstractnarration', '').\
               replace('\'', '').replace('\"', '')
    amount = int(award.get('awardamount', None))
    start_date = award.get('awardeffectivedate', '')
    end_date = award.get('awardexpirationdate', '')

    c.execute('''INSERT OR REPLACE INTO awards (award_id, title, abstract,
                                                amount, start_date, end_date)
                 VALUES ({}, "{}", "{}", {}, "{}", "{}");'''.format(
                 award_id, title, abstract, amount, start_date, end_date))

    for inv in award.get('investigator', []):
        first_name = inv.get('firstname', '').replace('\'', '').replace('\"', '')
        last_name = inv.get('lastname', '').replace('\'', '').replace('\"', '')
        email = inv.get('emailaddress', '').replace('\'', '').replace('\"', '')
        role = inv.get('rolecode', '').replace('\'', '').replace('\"', '')

        c.execute('''INSERT OR REPLACE INTO investigators (award_id, last_name,
                     first_name, role, email)
                     VALUES ({}, "{}", "{}", "{}", "{}");'''.format(
                     award_id, last_name, first_name, role, email))

    for inst in award.get('institution', []):
        name = inst.get('name', '').replace('\'', '').replace('\"', '')
        city = inst.get('cityname', '').replace('\'', '').replace('\"', '')
        state = inst.get('statename', '').replace('\'', '').replace('\"', '')
        state_code = inst.get('statecode', '').replace('\'', '').replace('\"', '')
        zipcode = inst.get('zipcode', '').replace('\'', '').replace('\"', '')
        country = inst.get('countryname', '').replace('\'', '').replace('\"', '')

        c.execute('''INSERT OR REPLACE INTO institutions (award_id, name,
                     city, state, state_code, zipcode, country)
                     VALUES ({}, "{}", "{}", "{}", "{}", "{}", "{}");'''.format(
                     award_id, name, city, state, state_code, zipcode, country))

    for org in award.get('organization', []):
        organization_code = org.get('code', None)
        directorate = org.get('directorate', None)
        division = org.get('division', None)

        c.execute('''INSERT OR REPLACE INTO organizations (award_id,
                     organization_code, directorate, division)
                     VALUES ({}, {}, "{}", "{}");'''.format(
                     award_id, organization_code, directorate, division))


if __name__=="__main__":
    num_args = len(sys.argv)

    if not num_args == 1:
        print("usage: python3 " + sys.argv[0] + "\n Populates initial "
                "database of CDC and NIH grants.")
        sys.exit(0)

    setup_database()