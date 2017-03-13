# NSF Database Utility
#
# Mark Saddler / MVR
#

import sys
import sqlite3
import re
import string
import nltk
from nltk.collocations import *
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from nltk.stem.porter import PorterStemmer

def keyword_search(keyword_list, db_cursor=None):
    '''
    Inputs:
        keyword_list (list of strings) : list of keywords to search for
        db_cursor (SQLite3 Cursor) : Cursor object for nsf.db
    Returns:
        award_id_set (set of strings) : set of award_id strings corresponding
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
        award_id (string)
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
    Returns a list of all titles and a list of all abstracts for the
    list of awards specified by 'award_id_list'.

    Inputs:
        award_id_list (list of strings) : award_id strings from which
                                          to fetch text
        db_cursor (sqlite3 cursor) : points to database
    Returns:
        title_list (list of strings)
        abstract_list (list of strings)
    '''
    title_list = []
    abstract_list = []
    for award_id in award_id_list:
        text_dict = get_fields_from_award_id(
                    award_id, ['title', 'abstract'], db_cursor)
        title_list.append(text_dict.get('title'))
        abstract_list.append(text_dict.get('abstract'))
    return (title_list, abstract_list)


def get_repeated_trigrams(title_list, abstract_list, min_rep, max_return):
    text = '\n'.join(title_list + abstract_list)
    text = re.sub(r'[{}]'.format(string.punctuation), '', text)
    tokens = nltk.wordpunct_tokenize(text)
    words = [w for w in tokens if not w in stopwords.words('english')]
    finder = TrigramCollocationFinder.from_words(words)
    finder.apply_freq_filter(min_rep)
    trigram_measures = nltk.collocations.TrigramAssocMeasures()
    scored = finder.score_ngrams(trigram_measures.raw_freq)

    trigram_list = [(trigram, score) for trigram, score in scored]
    trigram_list = sorted(trigram_list, key = lambda x: x[1])
    trigram_list = [trigram for trigram, score in trigram_list]
    trigram_list = trigram_list[0: min(max_return, len(trigram_list))]
    return trigram_list


def search_database_for_trigrams(db_filename, keyword_list, min_rep = 2, max_return = 50):
    conn = sqlite3.connect(db_filename)
    c = conn.cursor()

    award_id_set = keyword_search(keyword_list, c)
    award_id_list = list(award_id_set)

    (t_list, a_list) = get_all_text_from_award_id_list(award_id_list, c)
    trigrams = get_repeated_trigrams(t_list, a_list, min_rep, max_return)
    return trigrams

    #
    # Do something with trigrams
    #
    #

    conn.commit() # Save database
    conn.close() # Close database


if __name__=="__main__":

    #
    # This is mainly for debugging. Feel free to remove and import this file to use
    # its functions
    #

    num_args = len(sys.argv)

    usage = ("usage: python3 " + sys.argv[0] + " <database.db> <term1> <term2> ..." +
                 '\n\tPlease provide database filename and \
                  \n\tkeywords to search for (separated by space)')

    if num_args > 2:
        db_filename = sys.argv[1]
        keyword_list = sys.argv[2:num_args]
        trigrams = search_database_for_trigrams(db_filename, keyword_list)
        print('= == === ==== RESULTS ==== === == =')
        for t in trigrams:
            print(t)
        
    else:
        print(usage)
        sys.exit(0)



###########################################################################################
#   RETIRED CODE
#   (was supposed to be a faster method of searching for keywords)

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