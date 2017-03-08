# Code to add keyword_index to award database 
#
# Mark Saddler
#

import os
import sqlite3
import re

INDEX_IGNORE = set(['a', 'also', 'an', 'and', 'are', 'as', 'at', 'be',
                    'but', 'by', 'for', 'from', 'how', 'i',
                    'in', 'include', 'is', 'it', 'if', 'not', 'of',
                    'on', 'or', 'so',
                    'such', 'that', 'the', 'their', 'then', 'this', 'through', 'to',
                    'we', 'were', 'which', 'will', 'with', 'yet'])


db_filename = 'nsf_search.db' # <--- File name of NSF database
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
                     VALUES ({}, "{}");'''.format(award_id, keyword))

print('COMPLETE')
conn.commit() # Save database
conn.close() # Close database