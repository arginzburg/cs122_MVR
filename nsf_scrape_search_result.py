# Code to scrape downloaded NSF search data (single XML file)
#
# Mark Saddler
#

import os
import bs4
import sqlite3


def get_soup_from_xml_filename(fn):
    '''
    Convert XML file into a BeautifulSoup object
    '''
    soup = None
    if fn.endswith('.xml'):
        soup = bs4.BeautifulSoup(open(fn), "lxml")
    return soup


def parse_soup(soup):
    '''
    '''
    award_dict_list = []
    award_soup_list = soup.findAll('award')

    for award_soup in award_soup_list:
        award = {}
        tag = award_soup.find("awardnumber")
        while not tag is None:
            award[tag.name] = tag.text.strip()
            tag = tag.next_sibling.next_sibling
        award_dict_list.append(award)
    return award_dict_list


def init_db(db_filename):
    '''
    '''
    # print('PREPARING DATABASE: ', db_filename)
    create_new_tables = True
    if os.path.isfile(db_filename):
        create_new_tables = False
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    if create_new_tables:
        c.execute('''CREATE TABLE awards
                    (award_id text,
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


def add_award_to_db(award, c):
    '''
    Take in a dictionary (award), which contains all of the fields parsed from
    a single XML file, and insert all fields into the NSF database.
    '''
    award_id = int(award.get('awardnumber', None))
    title = award.get('title', '').\
            replace('\'', '').replace('\"', '')
    abstract = award.get('abstract', '').\
               replace('\'', '').replace('\"', '')
    amount = int(award.get('awardedamounttodate', None))
    start_date = award.get('startdate', '')
    end_date = award.get('enddate', '')

    c.execute('''INSERT OR REPLACE INTO awards (award_id, title, abstract,
                                                amount, start_date, end_date)
                 VALUES (?, ?, ?, ?, ?, ?);''',
                 (award_id, title, abstract, amount, start_date, end_date))

    name = award.get('principalinvestigator', '').replace('\'', '').replace('\"', '')
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
    email = award.get('piemailaddress', '').replace('\'', '').replace('\"', '')
    role = 'PI'

    c.execute('''INSERT OR REPLACE INTO investigators (award_id, last_name,
                     first_name, role, email)
                     VALUES (?, ?, ?, ?, ?);''',
                     (award_id, last_name, first_name, role, email))

    name = award.get('organization', '').replace('\'', '').replace('\"', '')
    city = award.get('organizationcity', '').replace('\'', '').replace('\"', '')
    state_code = award.get('organizationstate', '').replace('\'', '').replace('\"', '')
    zipcode = award.get('organizationzip', '').replace('\'', '').replace('\"', '')
    country = ''
    address = award.get('organizationstreet', '').replace('\'', '').replace('\"', '')

    c.execute('''INSERT OR REPLACE INTO institutions (award_id, name,
                 city, address, state, zipcode, country)
                 VALUES (?, ?, ?, ?, ?, ?, ?);''',
                 (award_id, name, city, address, state_code, zipcode, country))

    organization_code = None
    directorate = award.get('nsfdirectorate', None)
    division = award.get('nsforganization', None)

    c.execute('''INSERT OR REPLACE INTO organizations (award_id,
                     organization_code, directorate, division)
                     VALUES (?, ?, ?, ?);''',
                     (award_id, organization_code, directorate, division))


def run_search_scraper(search_xml_file, db_filename):
    '''
    '''
    (conn, c) = init_db(db_filename)
    soup = get_soup_from_xml_filename(search_xml_file)
    award_dict_list = parse_soup(soup)
    for award_dict in award_dict_list:
        add_award_to_db(award_dict, c)
    # print('Completed parsing file: ' + search_xml_file)
    conn.commit() # Save database
    conn.close() # Close database


##############################################################################
# Run script
##############################################################################

if __name__=="__main__":
  search_xml_file = "/home/student/cs122_MVR/Awards.xml"
  db_filename = 'nsf_search.db' # <--- File name of temp NSF search database
  run_search_scraper(search_xml_file, db_filename)
