# Code to add keyword_index to award databases
#
# Mark Saddler / MVR
#

import sys
import os
import sqlite3
import re

INDEX_IGNORE = set(['a', 'also', 'an', 'and', 'are', 'as', 'at', 'be',
                    'but', 'by', 'for', 'from', 'how', 'i',
                    'in', 'include', 'is', 'it', 'if', 'not', 'of',
                    'on', 'or', 'so',
                    'such', 'that', 'the', 'their', 'then', 'this', 'through', 'to',
                    'we', 'were', 'which', 'will', 'with', 'yet'])


def add_and_populate_index_table(db_filename):
    '''
    Takes in a SQL database filename and builds a keyword index from all words
    in the award titles and abstacts. This index is added to the database as a
    new table (keyword_index).
    '''
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS keyword_index
                 (award_id int,
                  keyword text,
                  constraint fk_index foreign key (award_id)
                  references awards (award_id));''')

    c.execute('''SELECT award_id, title, abstract from awards;''')
    title_list = c.fetchall()
    print('Processing', len(title_list), 'Awards')

    for i, (award_id, tmp_title, tmp_abstract) in enumerate(title_list):

        tmp_str = tmp_title + ' ' + tmp_abstract
        tmp_str = re.sub(r'[^\w\s]', '', tmp_str)

        words = set(tmp_str.split())
        words = [w.strip() for w in words if w.strip() not in INDEX_IGNORE]

        for w in words:
            if w.isupper():
                keyword = w
            else:
                keyword = w.lower()
    
            c.execute('''INSERT OR REPLACE INTO keyword_index (award_id, keyword)
                         VALUES (?, ?);''', (award_id, keyword))

    print('COMPLETE: Index has been added to ' + db_filename)
    conn.commit() # Save database
    conn.close() # Close database



if __name__=="__main__":
    num_args = len(sys.argv)

    usage = ("usage: python3 " + sys.argv[0] + " <database.db>" +
            "\n\t Adds a keyword_index table to the provided database \
             \n\t and populates it with words from titles/abstracts")

    if num_args == 2:
        db_filename = sys.argv[1]
        add_and_populate_index_table(db_filename)
        
    else:
        print(usage)
        sys.exit(0)