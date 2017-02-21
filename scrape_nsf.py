# Code to scrape downloaded NSF data (XML files)
#
# Mark Saddler
#

import os
import bs4
import sqlite3

import re
import sys
import csv


def get_list_of_xml_filenames(path):
    file_list = os.listdir(path)
    xml_filenames = []
    for name in file_list:
        if name.endswith('.xml'):
            xml_filenames.append(path + name)
    return xml_filenames


def get_soup_from_xml_filename(fn):
    soup = None
    if fn.endswith('.xml'):
        soup = bs4.BeautifulSoup(open(fn))
    return soup


def parse_soup(soup):
    award = {}
    tag = soup.find("awardtitle")
    subdivided_tags = ['investigator', 'institution',
                       'organization', 'programelement', 'programreference']
    while not tag is None:
        if tag.name == 'awardinstrument':
            tmp_list = award.get(tag.name, [])
            child_tags = tag.findChildren()
            for child in child_tags:
                tmp_list.append(child.text.strip())
            award[tag.name] = tmp_list
        elif tag.name in subdivided_tags:
            parse_subdivided_tag(tag, award)
        else:
            award[tag.name] = tag.text.strip()
        tag = tag.next_sibling.next_sibling
    return award


def parse_subdivided_tag(tag, award_dict):
    tmp_list = award_dict.get(tag.name, [])
    sub_dict = {}
    child_tags = tag.findChildren()
    for child in child_tags:
        value = child.text.strip()
        if len(value) > 0:
            sub_dict[child.name] = value
    tmp_list.append(sub_dict)
    award_dict[tag.name] = tmp_list


def init_db(db_filename):
    create_new_tables = True
    if os.path.isfile(db_filename):
        create_new_tables = False
    conn = sqlite3.connect('nsf.db')
    c = conn.cursor()
    if create_new_tables:
        c.execute('''CREATE TABLE awards
                    (award_id int,
                     title text,
                     abstract text,
                     amount int,
                     start_date char(10),
                     end_date char(10),
                     constraint pk_awards primary key (award_id));''')
        c.execute('''CREATE TABLE investigators
                     (award_id int,
                      last_name text,
                      first_name text,
                      role text,
                      email text,
                      constraint fk_investigators foreign key (award_id)
                      references awards (award_id));''')
        c.execute('''CREATE TABLE institutions
                     (award_id int,
                      name text,
                      city text,
                      state text,
                      state_code char(2),
                      zipcode text,
                      country text,
                      constraint fk_institutions foreign key (award_id)
                      references awards (award_id));''')
        c.execute('''CREATE TABLE organizations
                     (award_id int,
                      organization_code int,
                      directorate text,
                      division text,
                      constraint fk_organizations foreign key (award_id)
                      references awards (award_id));''')
    return (conn, c)


def add_award_to_db(award, c):
    award_id = int(award.get('awardid', None))
    title = award.get('awardtitle', '').\
            lower().replace('\'', '').replace('\"', '')
    abstract = award.get('abstractnarration', '').\
               lower().replace('\'', '').replace('\"', '')
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


##############################################################################
# Run script
##############################################################################

db_filename = 'nsf.db'
(conn, c) = init_db(db_filename)

years = [2013, 2014, 2015, 2016, 2017]

for year in years:

    data_path = 'data/nsf/{}/'.format(year)

    xml_list = get_list_of_xml_filenames(data_path)

    print('Processing path: ' + data_path)
    for xml_file in xml_list:
        soup = get_soup_from_xml_filename(xml_file)
        award_dict = parse_soup(soup)
        add_award_to_db(award_dict, c)
    print('Completed path: ' + data_path)

conn.commit() # Save database
conn.close() # Close database