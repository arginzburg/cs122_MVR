# CS122 Project
#
# Vishok Srikanth / MVR
# 
# Python functions to interact with the DHHS's TAGG Advanced Search form so
# that search returns contain data as we desire. Expects to interact with
# objects from JS_browser wrapper for Selenium Webdriver and pyVirtualDisplay.

import time

def search(browser, years = ['2017', '2016', '2015', '2014', '2013'],
    divisions = ['NIH', 'CDC'], states = [], usa = True , intl = True,
    keywords = ""):
    select_report_columns(browser)
    select_fiscal_years(browser, years)
    select_operating_divisions(browser, divisions)
    select_states(browser, states)
    select_region(browser, usa, intl)
    select_keywords(browser, keywords)
    time.sleep(1)
    browser.click('//*[@id="btn_AdvSearch_CD"]') # Click the "Search" button.


def select_report_columns(browser):
    '''
    Selects the checkboxes corresponding to the report columns we want on the
    DHHS's TAGG Advanced Search page, given a JS_browser navigated onto that
    page. We always want all these fields, so no further inputs are needed
    to control this function. The fields it actually selects contain:
        Operating Division, Recipient Name, Recipient Address, Recipient City,
        Recipient State, Recipient ZIP Code, Recipient Country, Award Number,
        Award Title, Action Issue Date, CFDA Program Name,
        Principal Investigator
    However, it clicks different checkboxes than these since some of these are
    selected by default, along with some boxes we don't want.
    '''
    delta_paths = ['//*[@id="cbl_Columns_RB0_I"]',   # - Fiscal Year
                    '//*[@id="cbl_Columns_RB4_I"]',  # + Recipient Address
                    '//*[@id="cbl_Columns_RB12_I"]', # + Recipient City
                    '//*[@id="cbl_Columns_RB28_I"]', # + Recipient ZIP Code
                    '//*[@id="cbl_Columns_RB17_I"]', # + Recipient Country
                    '//*[@id="cbl_Columns_RB6_I"]',  # + Action Issue Date
                    '//*[@id="cbl_Columns_RB3_I"]',  # - CFDA Program Number
                    '//*[@id="cbl_Columns_RB19_I"]'] # + Principal Investigator
    for path in delta_paths:
        browser.click(path, force_load_wait = 0)


def select_fiscal_years(browser, years = []):
    '''
    Selects the checkboxes corresponding to the fiscal years we want to include
    in the search returned from the DHHS's TAGG Advanced Search page, given a
    JS_browser nagivated onto that page. "years" may be list of int or str.
    '''
    # Make sure to prevent users from choosing bad inputs in the Django UI.
    options = ['2017', '2016', '2015', '2014', '2013', '2012', '2011', '2010',
                '2009', '2008', '2007', '2006', '2005', '2004', '2003', '2002',
                '2001', '2000', '1999', '1998', '1997', '1996', '1995', '1994',
                '1993', '1991']
    # Determined empirically by examining the page.                   
    paths = ['//*[@id="lst_FYs_LBI{}C"]/input'.format(x) for x in range(0, 26)]
    # This is a little inefficient compared to explicitly defining the
    # dictionary, but not so important in the grand scheme of things.
    year_path_dict = option_path_dict(options, paths)
    # 2017 is checked when the page loads. Rectify this.
    browser.click(year_path_dict["2017"], force_load_wait = 0)
    for year in years:
        browser.click(year_path_dict[str(year)], force_load_wait = 0)
    time.sleep(10)   # Give other fields/boxes time to reload in response.


def select_operating_divisions(browser, divisions = []):
    '''
    Selects the checkboxes corresponding to the operating divisions we want to
    include in the search returned from the DHHS's TAGG Advanced Search page,
    given a JS_browser nagivated onto that page. "divisions" should be a list
    of strings.
    '''
    # Make sure to prevent users from choosing bad inputs in the Django UI.
    options = ['AHRQ', 'CDC', 'FDA', 'NIH']
    # Determined empirically by examining the page.
    paths = ['//*[@id="lst_ParentOrgs_LBI{}C"]/input'.format(x)
                for x in [13, 15, 18, 21]]
    # This is a little inefficient compared to explicitly defining the
    # dictionary, but not so important in the grand scheme of things.
    division_path_dict = option_path_dict(options, paths)

    for division in divisions:
        browser.click(division_path_dict[division], force_load_wait = 0)


def select_states(browser, states = []):
    '''
    Selects the checkboxes corresponding to the recipient states we want to
    include in the search returned from the DHHS's TAGG Advanced Search page,
    given a JS_browser nagivated onto that page. "states" should be a list of
    strings.
    '''
    # Make sure to prevent users from choosing bad inputs in the Django UI.
    options = ['AL', 'AK', 'AS', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC',
                'FM', 'FL', 'GA', 'GU', 'HI', 'ID', 'IL', 'IN', 'IA', 'JQ',
                'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', 'MS', 'MO',
                'MT', 'MQ', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND',
                'MP', 'BQ', 'OH', 'OK', 'OR', 'PA', 'PR', 'MH', 'PW', 'RI',
                'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VI', 'VA', 'WA', 'WV',
                'WI', 'WY', 'WQ']
    # Determined empirically by examining the page. 
    paths = ['//*[@id="lst_States_LBI{}C"]/input'.format(x)
                for x in range(0, 63)]
    # This is a little inefficient compared to explicitly defining the
    # dictionary, but not so important in the grand scheme of things.
    state_path_dict = option_path_dict(options, paths)

    for state in states:
        browser.click(state_path_dict[state], force_load_wait = 0)


def select_region(browser, usa = True, intl = True):
    '''
    Selects the checkboxes corresponding to the recipient countries we want to
    include in the search returned from the DHHS's TAGG Advanced Search page,
    given a JS_browser nagivated onto that page. "usa" and "intl" should be
    Boolean based on whether countries in these categories should be included.
    '''
    if usa and intl:
        # Checking every box and checking no box will have the same effect.
        return None
    else:
        USofA_path = '//*[@id="lst_Countries_LBI197C"]/input'
        intl_paths = ['//*[@id="lst_Countries_LBI{}C"]/input'.format(x)
                        for x in range(0, 211) if x != 197]
        if usa:
            browser.click(USofA_path, force_load_wait = 0)
        if intl:
            for path in intl_paths:
                browser.click(path, force_load_wait = 0)


def select_keywords(browser, keywords):
    '''
    Inputs a list of keywords into the "Award Abstract Text" field of the
    DHHS's TAGG Advanced Search page, given a JS_browser nagivated onto that
    page. 
    '''
    if keywords:
        browser.enter_text('//*[@id="s_AbstractText_I"]', keywords)


def option_path_dict(options, paths):
    '''
    Stitches dictionaries with options and paths from lists that are
    appropriately ordered. Generating dictionaries like this is a little
    inefficient since we could just explicitly list these dictionaries, but
    that feels more distastefully hard-coded and would result in a really long
    file that wasn't really readable at a quick glance.
    '''
    return {option: path for (option, path) in zip(options, paths)}
