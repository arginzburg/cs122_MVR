# NSF Database Utility
#
# Mark Saddler
#

import sqlite3
import re

def keyword_search(keyword_list, db_cursor=None):
    '''
    Inputs:
        keyword_list (list of strings) : list of keywords to search for
        db_cursor (SQLite3 Cursor) : Cursor object for nsf.db
    Returns:

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
            award_ids = id_dict[kw]
        else:
            award_ids = award_ids.intersection(id_dict[kw])
    return award_ids


db_filename = 'nsf.db' # <--- File name of NSF database
conn = sqlite3.connect('nsf.db')
c = conn.cursor()

keyword_list = ['structural', 'biochemistry']
keyword_search(keyword_list, c)

conn.commit() # Save database
conn.close() # Close database



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

    #results = db_cursor.execute(sql_str)
    #print(results.fetchall())