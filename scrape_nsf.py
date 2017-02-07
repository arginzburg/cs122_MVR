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
            print('Lonely tag = ' + tag.name + ' = ' + tag.text)
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
                     constraint pk_awards primary key (award_id))''')
        c.execute('''CREATE TABLE investigators
                     (award_id int,
                      last_name text,
                      first_name text,
                      role text,
                      email text,
                      constraint fk_investigators foreign key (award_id)
                      references awards (award_id))''')
        c.execute('''CREATE TABLE institutions
                     (award_id int,
                      name text,
                      city text,
                      state text,
                      state_code char(2),
                      zipcode int,
                      country text,
                      constraint fk_institutions foreign key (award_id)
                      references awards (award_id))''')
        c.execute('''CREATE TABLE organizations
                     (award_id int,
                      organization_code int,
                      directorate text,
                      division text,
                      constraint fk_organizations foreign key (award_id)
                      references awards (award_id))''')
    return (conn, c)



##############################################################################
# Run script
##############################################################################

data_path = 'data/nsf/2016/'
db_filename = 'nsf.db'

(conn, c) = init_db(db_filename)

xml_list = get_list_of_xml_filenames(data_path)

conn.commit() # Save database
conn.close() # Close database

soup = get_soup_from_xml_filename(xml_list[0])
a = parse_soup(soup)
print(a)