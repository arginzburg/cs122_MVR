# NSF Database Utility
#
# Mark Saddler
#

import sqlite3
import re
import nltk
from nltk.collocations import *

def keyword_search(keyword_list, db_cursor=None):
    '''
    Inputs:
        keyword_list (list of strings) : list of keywords to search for
        db_cursor (SQLite3 Cursor) : Cursor object for nsf.db
    Returns:
        award_id_set (set of integers) : set of award_id integers corresponding
            to awards in the NSF database that match all keywords
    '''
    id_dict = {}
    sql_query = 'SELECT award_id FROM keyword_index WHERE keyword = ?'
    for kw in keyword_list:
        results = db_cursor.execute(sql_query, [kw])
        results = results.fetchall()
        results = set([award_id for (award_id,) in results])
        id_dict[kw] = results
    for count, kw in enumerate(id_dict.keys()):
        if count == 0:
            award_id_set = id_dict[kw]
        else:
            award_id_set = award_id_set.intersection(id_dict[kw])
    return award_id_set


def get_fields_from_award_id(award_id, fields, db_cursor):
    '''
    Inputs:
        award_id (integer)
        fields (list of strings) : column names in awards table
        db_cursor (sqlite3 cursor) : points to database with awards table
    Returns:
        rv (dictionary) : field-keyed dictionary of the values in the
            database for the award specified by award_id
    '''
    selection = ', '.join(fields)
    sql_query = 'SELECT {} FROM awards WHERE award_id = ?'.format(selection)
    results = db_cursor.execute(sql_query, [award_id])
    results = results.fetchall()
    rv = {}
    for i, field in enumerate(fields):
        rv[field] = results[0][i]
    return rv


def get_all_text_from_award_id_list(award_id_list, db_cursor):
    '''
    '''
    title_list = []
    abstract_list = []
    for award_id in award_id_list:
        text_dict = get_fields_from_award_id(
                    award_id, ['title', 'abstract'], db_cursor)
        title_list.append(text_dict.get('title'))
        abstract_list.append(text_dict.get('abstract'))
    return (title_list, abstract_list)




db_filename = 'nsf.db' # <--- File name of NSF database
conn = sqlite3.connect('nsf.db')
c = conn.cursor()

keyword_list = ['structural', 'biochemistry']
award_id_set = keyword_search(keyword_list, c)
award_id_list = list(award_id_set)
award_id_list = award_id_list[0:3]

get_all_text_from_award_id_list(award_id_list, c)

conn.commit() # Save database
conn.close() # Close database









#
#   RETIRED CODE
#

def keyword_search_nested(keyword_list, db_cursor=None):
    '''
    Inputs:
        keyword_list (list of strings) : list of keywords to search for
        db_cursor (SQLite3 Cursor) : Cursor object for nsf.db
    '''

    selections = ['award_id', 'title', 'abstract']
    select_str = ", ".join(selections)
    select_str = 'award_id'

    sql_str = 'SELECT {} FROM ({});'.format(select_str, '{}')
    print(sql_str)

    counter = 0
    for kw in keyword_list:
        print(kw)
        counter += 1

        kw_str = '''SELECT award_id FROM ({})
                    INNER JOIN keyword_index as ki{} USING (award_id)
                    WHERE ki{}.keyword = "{}"'''.format('{}', counter, counter, kw)

        sql_str = sql_str.format(kw_str)

    sql_str = sql_str.format('awards')
    print(sql_str)