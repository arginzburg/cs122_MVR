# Code to scrape downloaded NSF data (XML files)
#
# Mark Saddler
#

import os

import re
import bs4
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
    award_tag = soup.find("award")
    children = award_tag.findChildren()
    for child_tag in children:
        award[child_tag.name] = child_tag.text
    return award


path = 'data/nsf/2016/'
xml_list = get_list_of_xml_filenames(path)
soup = get_soup_from_xml_filename(xml_list[0])
a = parse_soup(soup)

for key in a.keys():
    print(key + ' = ' + a[key])