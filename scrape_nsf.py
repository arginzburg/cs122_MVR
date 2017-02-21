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
        sub_dict[child.name] = child.text.strip()
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
                      zipcode int,
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
    award_id = award.get('awardid', None)
    title = award.get('awardtitle', None).lower().strip()
    abstract = award.get('abstractnarration', None).lower().strip()
    amount = award.get('awardamount', None)
    start_date = award.get('awardeffectivedate', None)
    end_date = award.get('awardexpirationdate', None)

    c.execute('''INSERT OR REPLACE INTO awards (award_id, title, abstract,
                                                amount, start_date, end_date)
                 VALUES ({}, "{}", "{}", {}, "{}", "{}");'''.format(
                 award_id, title, abstract, amount, start_date, end_date))

    for inv in award.get('investigator', []):
        first_name = inv.get('firstname', None)
        last_name = inv.get('lastname', None)
        email = inv.get('emailaddress', None)
        role = inv.get('rolecode', None)

        c.execute('''INSERT OR REPLACE INTO investigators (award_id, last_name,
                     first_name, role, email)
                     VALUES ({}, "{}", "{}", "{}", "{}");'''.format(
                     award_id, last_name, first_name, role, email))

    for inst in award.get('institution', []):
        name = inst.get('name', None)
        city = inst.get('cityname', None)
        state = inst.get('statename', None)
        state_code = inst.get('statecode', None)
        zipcode = inst.get('zipcode', None)
        country = inst.get('countryname', None)

        c.execute('''INSERT OR REPLACE INTO institutions (award_id, name,
                     city, state, state_code, zipcode, country)
                     VALUES ({}, "{}", "{}", "{}", "{}", {}, "{}");'''.format(
                     award_id, name, city, state, state_code, zipcode, country))

    for org in award.get('organization', []):
        organization_code = org.get('code', None)
        directorate = org.get('directorate', None)
        division = org.get('division', None)

        print(organization_code)
        print(directorate)
        print(division)

        c.execute('''INSERT OR REPLACE INTO organizations (award_id,
                     organization_code, directorate, division)
                     VALUES ({}, {}, "{}", "{}");'''.format(
                     award_id, organization_code, directorate, division))


##############################################################################
# Run script
##############################################################################

data_path = 'data/nsf/2016/'
db_filename = 'nsf.db'

(conn, c) = init_db(db_filename)

xml_list = get_list_of_xml_filenames(data_path)

soup = get_soup_from_xml_filename(xml_list[0])
a = parse_soup(soup)
for key in a.keys():
    print(key + ' <><><> ' + str(a[key]))
    print('')

add_award_to_db(a, c)

conn.commit() # Save database
conn.close() # Close database