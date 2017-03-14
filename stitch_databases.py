# stitch_databases.py
#
# Mark Saddler, Vishok Srikanth / MVR
#
# Script to build single federal funding database (to interface with Django website)
#   This file will take build a ~2gb database: MVR.db containing all of the on-site
#   stored data.

import sqlite3

db_filename = 'MVR.db'
dbs = ['nsf.db', 'taggs_2013.db', 'taggs_2014.db', 'taggs_2015.db', 'taggs_2016.db', 'taggs_2017.db']
table_list = ['awards', 'investigators', 'institutions', 'organizations', 'keyword_index']

def initialize_db(db_filename):
    '''
    See notes below and in collect_TAGG.py about how much this function is my
    work (it's called "connect_db" there and does something very slightly
    different). Here I've copied it rather than importing because I needed to
    add the "counter" to each table. This has to be in each table, since we 
    need to distinguish between cached copies of records that resulted from 
    different searches.

    Initialize the cached award database, which has the following tables:
        awards, investigators, institutions, organizations, record_counter
    See sqlite3 commands below to see how these tables are linked.

    Mostly copied from MS's work in scrape_nsf.py. Can't import it because at
    time of writing this, that script contains code at the end outside any
    function or loop that I don't want to run when this script gets used.
    '''
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()
    c.execute('''CREATE TABLE awards
                (award_id text,
                 agency text,
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
    c.execute('''CREATE TABLE keyword_index
                 (award_id int,
                  keyword text,
                  constraint fk_index foreign key (award_id)
                  references awards (award_id));''')
    return (conn, c)


(conn, c) = initialize_db(db_filename)

for tmp_db in ['nsf.db']:
    tmp_conn = sqlite3.connect(tmp_db)
    tmp_c = tmp_conn.cursor()
    #tmp_c.execute('ALTER TABLE awards ADD agency text')
    tmp_c.execute('UPDATE awards SET agency =(?)', ['NSF'])
    tmp_conn.commit()
    tmp_conn.close()

counter = 0
for tmp_db in dbs:
    counter += 1
    print('=== ATTACHING: ', tmp_db, '===')
    c.execute('ATTACH "{}" as tmp_db{}'.format(tmp_db, counter))
    for table in table_list:
        print('============= MERGING: ', table)
        c.execute('INSERT OR REPLACE INTO main.{} SELECT * FROM tmp_db{}.{}'.format(table, counter, table))

conn.commit()
conn.close()