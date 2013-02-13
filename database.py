#!/usr/bin/env python
"""
database.py
Author: Brian Boates

Build a MySQL database of background words
and query words from Indeed.com job postings
for skillrank analysis

DATABASE: "skillrank"
TABLES:         COLUMNS:
bkgd_jobkeys:   id | jobkey
bkgd_words:     id | term   | count
"""
import os, sys
import MySQLdb as mdb
import indeed, utils, analysis

def dbRemove(db='skillrank'):
    """
    WARNING! This function will drop current skillrank database
    """
    # connect to MySQL
    con = mdb.connect(host='localhost', user='root')
    
    # create cursor for MySQL
    cur = con.cursor()
    
    # check to see if skillrank database exists
    cur.execute("SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = \'"+db+"\'")
    exists = cur.fetchone()
    
    # if skillrank database exists, remove it entirely
    if exists:
        cur.execute("DROP database "+db)


def dbCreate(db='skillrank'):
    """
    Create the MySQL skillrank database
    """
    # connect to MySQL
    con = mdb.connect(host='localhost', user='root')
    
    # create cursor for MySQL
    cur = con.cursor()
    
    # create the skillrank database if not already present
    cur.execute("CREATE SCHEMA IF NOT EXISTS "+db)
    
    # change to newly created skillrank database
    cur.execute("USE "+db)
    
    # with connection to the skillrank database
    with con:
        
        # create cursor to skillrank database        
        cur = con.cursor()
        
        #==================================================#
        ################ CREATE BKGD TABLES ################
        #==================================================#
        
        # create bkgd_jobkeys table: id (primary key) | jobkey
        # indeed.com jobkeys are 16 characters long
        cur.execute("CREATE TABLE IF NOT EXISTS \
                     bkgd_jobkeys(id INT PRIMARY KEY AUTO_INCREMENT, \
                                  jobkey CHAR(16))")
                              
        # create bkgd_words table: id (primary key) | term | count
        cur.execute("CREATE TABLE IF NOT EXISTS \
                     bkgd_words(id INT PRIMARY KEY AUTO_INCREMENT, \
                                term VARCHAR(64), count INT)")
                                
        # create bkgd_bigrams table: id (primary key) | term | count
#        cur.execute("CREATE TABLE IF NOT EXISTS \
#                     bkgd_bigrams(id INT PRIMARY KEY AUTO_INCREMENT, \
#                                  term VARCHAR(64), count INT)")
                                  
        # create bkgd_trigrams table: id (primary key) | term | count
#        cur.execute("CREATE TABLE IF NOT EXISTS \
#                     bkgd_trigrams(id INT PRIMARY KEY AUTO_INCREMENT, \
#                                   term VARCHAR(64), count INT)")
                                   
        #===================================================#        
        ################ CREATE QUERY TABLES ################
        #===================================================#        
        
        # create q_jobkeys table: id (primary key) | jobkey
        # indeed.com jobkeys are 16 characters long
#        cur.execute("CREATE TABLE IF NOT EXISTS \
#                     q_jobkeys(id INT PRIMARY KEY AUTO_INCREMENT, \
#                               jobkey CHAR(16))")
                              
        # create q_words table: id (primary key) | term | count
#        cur.execute("CREATE TABLE IF NOT EXISTS \
#                     q_words(id INT PRIMARY KEY AUTO_INCREMENT, \
#                             term VARCHAR(64), count INT, relevance DECIMAL(10,8))")
                             
        # create q_bigrams table: id (primary key) | term | count
#        cur.execute("CREATE TABLE IF NOT EXISTS \
#                     q_bigrams(id INT PRIMARY KEY AUTO_INCREMENT, \
#                               term VARCHAR(64), count INT, relevance DECIMAL(10,8))")
                               
        # create q_trigrams table: id (primary key) | term | count
#        cur.execute("CREATE TABLE IF NOT EXISTS \
#                     q_trigrams(id INT PRIMARY KEY AUTO_INCREMENT, \
#                                term VARCHAR(64), count INT, relevance DECIMAL(10,8))")
                                
        #===================================================#
        
    # close cursor to skillrank database
    if cur: cur.close()
    
    # close connection to skillrank database
    if con: con.close()


def newJobkey(cur, jobkey, tableType):
    """
    Return True/False if jobkey is new/already in table
    params:
        cur: cursor to skillrank database
        jobkey: string | indeed.com unique job posting ID
        tableType: 0 = insert into bkgd tables
                   1 = insert into query tables
    """
    # use bkgd table if tableType=0
    if tableType == 0:
        jTable = 'bkgd_jobkeys'
        
    # use query table if tableType=1
    elif tableType == 1:
        jTable = 'q_jobkeys'
    
    # tableType must be 0 or 1, otherwise return 1 for failure
    else:
        return 'invalid tableType (0=bkgd, 1=query)'
        
    # check to see if jobkey exists
    cur.execute("SELECT * FROM "+jTable+" WHERE jobkey = \'"+jobkey+"\'")
    
    # True if jobkey is new, False if already present
    new = not cur.fetchone()
    
    return new


def updateTermCount(cur, table, term):
    """
    Update the count for a term in a given table
    or initialize to 1 if not already present
    return: 0 if table update was successful
            1 if table given was invalid
    params:
            cur:    cursor to skillrank database
            table:  skillrank db table to use
            term:   term to update in skillrank database
    options for table:
        bkgd_words, bkgd_bigrams, bkgd_trigrams, q_words, q_bigrams, q_trigrams
    """
    # options for table:
    tableOptions = ['bkgd_words', 'bkgd_bigrams', 'bkgd_trigrams', 
                                  'q_words', 'q_bigrams', 'q_trigrams']
                                  
    # if table is not valid, set report to 1 (i.e. failure)
    if table in tableOptions:
    
        # check to see if term is already in terms table
        cur.execute("SELECT * FROM "+table+" WHERE term = \'"+term+"\'")
        new = not cur.fetchone()
    
        # if term not in terms table
        if new:
            # insert term into term table with initial value of 1
            cur.execute("INSERT INTO "+table+"(term,count) VALUES(\'"+term+"\',1)")
    
        # if term is already in terms table
        else:
            # increment the term's count by 1
            cur.execute("UPDATE "+table+" SET count = count + 1 WHERE term = \'"+term+"\'")
            
        # if table update was successful, return 0 for success
        return 0
        
    # if table given is not a valid option, return 1 for failure
    else:
        return 1


def updateTermRelevance(cur, table, term):
    """
    Update the relevance for a term in a given table
    return: 0 if table update was successful
            1 if table given was invalid
    params:
            cur:    cursor to skillrank database
            table:  skillrank db table to use
            term:   term to update in skillrank database
    options for table:
        bkgd_words, bkgd_bigrams, bkgd_trigrams, q_words, q_bigrams, q_trigrams
    """
    # options for table:
    tableOptions = ['bkgd_words', 'bkgd_bigrams', 'bkgd_trigrams', 
                                  'q_words', 'q_bigrams', 'q_trigrams']
                                  
    # if table is not valid, set report to 1 (i.e. failure)
    if table in tableOptions:
        
        # compute the term's relevance
        R = analysis.relevance(cur, term)
        
        # update relevance of term in skillrank db
        cur.execute("UPDATE "+table+" SET relevance="+str(R)+" WHERE term=\'"+term+"\'")
            
        # if table update was successful, return 0 for success
        return 0
        
    # if table given is not a valid option, return 1 for failure
    else:
        return 1


def getRelevantTerms(table, N=20):
    """
    Retrieve the N most relevant terms from table
    return: list[tuple] | list of N most relevant terms in table
                        | each tuple = (term, relevance)
    params:
            table:  skillrank db table to use
            N:      number of most relevant terms to retrieve (default=20)
    """
    # connect to the skillrank database and create a cursor
    con = mdb.connect(host='localhost', user='root', db='skillrank')
    cur = con.cursor()
    
    # retrieve the N most relevant terms with their relevances
    cur.execute("SELECT term,relevance FROM "+table+" ORDER BY relevance DESC LIMIT "+str(N))
    topTerms = cur.fetchall()
    topTerms = list(topTerms)
    
    # close the database cursor and connection
    if cur: cur.close()
    if con: con.close()
    
    return topTerms


def getPostings(jobQuery, nURLs=1, start=0):
    """
    return: jobkeys  | list[string] | list of job postings unique ID
            allterms | list[list[string]] | list of list of words from job postings
    params:
            jobQuery: string | default empty string (generic job search)
            nJobs: int | number of job postings to search (default=499 (500 max allowed))
            start: int | index to begin api url search
    """
    # retrieve list of URL's for jobQuery
    urls = indeed.getJobURLs(jobQuery, nURLs=nURLs, start=start)
    
    # initialize lists for all terms and jobkeys
    allwords, jobkeys = [], []
    
    # loop over urls
    for url in urls:
        
        # retrieve information from URL's job posting
        jobkey, position, company, location, words = indeed.parseJobPosting(url)
        
        # append current job posting info to allwords and jobkeys
        jobkeys.append(jobkey)
        allwords.append(words)
        
    # only care about the jobkey and terms list for skillrank database
    return jobkeys, allwords


def insertPosting(cur, jobkey, words, tableType):
    """
    Insert words, bigrams, and trigrams from a single job posting
    into their respective tables
    return: 1 if tableType is invalid
            True if jobkey is new
            False if jobkey is not new
    params:
            cur: cursor to skillrank database
            jobkey: string | indeed.com unique job posting ID
            words: list[string] list of words from a single job posting
            tableType: 0 = insert into bkgd tables
                       1 = insert into query tables
    """
    # use bkgd tables if tableType=0
    if tableType == 0:
        jTable = 'bkgd_jobkeys'
        wTable, bTable, tTable = 'bkgd_words', 'bkgd_bigrams', 'bkgd_trigrams'
        
    # use query tables if tableType=1
    elif tableType == 1:
        jTable = 'q_jobkeys'
        wTable, bTable, tTable = 'q_words', 'q_bigrams', 'q_trigrams'
    
    # tableType must be 0 or 1, otherwise return 1 for failure
    else:
        return 1
        
    #======== DO THE INSERTION ========#
    
    # check to see if jobkey is new
    if newJobkey(cur, jobkey, tableType=tableType):
        
        # if new, insert jobkey into jobkeys table
        cur.execute("INSERT INTO "+jTable+"(jobkey) VALUES(\'"+jobkey+"\')")
        
        # create bigrams and trigrams lists
#        bigrams  = utils.getNgrams(words, N=2)     # 500 / 514?? postings used!!!
#        trigrams = utils.getNgrams(words, N=3)   # 450 postings used !!!!
        
        # update word counts
        for word in words:
            val = updateTermCount(cur=cur, table=wTable, term=word)
            
        # update bigram counts
#        for bigram in bigrams:
#            val = updateTermCount(cur=cur, table=bTable, term=bigram)
            
        # update trigram counts
#        for trigram in trigrams:
#            val = updateTermCount(cur=cur, table=tTable, term=trigram)
            
        # if it is for the query table, also update the relevance column
        if tableType == 1:
            
            # update word relevances
            for word in words:
                val = updateTermRelevance(cur=cur, table=wTable, term=word)
            
            # update bigram relevances
#            for bigram in bigrams:
#                val = updateTermRelevance(cur=cur, table=bTable, term=bigram)
            
            # update trigram relevances
#            for trigram in trigrams:
#                val = updateTermRelevance(cur=cur, table=tTable, term=trigram)
            
        # return true if jobkey is new and insertion was performed
        return True
    
    # if jobkey is not new, ignore the posting and return false
    else:
        return False


def populateTables(jobQuery, tableType, nJobs=1, start=0):
    """
    Populate tables with words from job postings
    return: 
    params:
            tableType: 0 = insert into bkgd tables
                       1 = insert into query tables
            nURLs: int | number of job URL's to retrieve
            start: int | index for api job search starting point
    """
    # connect to the skillrank database
    con = mdb.connect(host='localhost', user='root', db='skillrank')
    
    # create cursor for the skillrank database
    cur = con.cursor()
    
    # create index to track number of unique job postings 
    # inserted into the database tables
    nUnique = 0
    
    # initial number of URL's to try is just nJobs
    nURLs = nJobs
    
    # with connection to the bkgd database
    with con:
        
        # continue until unique jobs entered into DB = nJobs requested by user 
        while nUnique < nJobs:
            
            # retrieve jobkeys and words from job postings
            jobkeys, allwords = getPostings(jobQuery=jobQuery, nURLs=1000, start=0)
    
            # add jobkeys to jobkeys table in bkgd database
            for i in range(len(jobkeys)):
            
                # select current jobkey and words list
                jobkey = jobkeys[i]
                words  = allwords[i]
                
                # insert the current job posting into its respective 
                # jobkeys, words, bigrams, and trigrams tables
                val = insertPosting(cur, jobkey, words, tableType=tableType)
                
                # if val is True, posting was new ---> increment nUnique
                if val:
                    nUnique += 1
                    print "done", nUnique, "out of", nJobs, "| i =", i
                else:
                    print "not unique - still at", nUnique, "out of", nJobs
                    print "| i =", i, "out of", len(jobkeys), "start =", start
    
            # reset nURLs to number of jobs requested minus unique jobs found so far
            nURLs = nJobs - nUnique
            
            # increment start variable to avoid the same URL's as before
            start += 100
            
            # api limited to 1000 job postings total
            if start >= 1100: break
    
    # close the database cursor
    if cur: cur.close()
    
    # close the database connection
    if con: con.close()


def main():
    
    # retrieve user input
    try:
        jobQuery  = sys.argv[1]
        tableType = int(sys.argv[2])
        nJobs     = int(sys.argv[3])
        start     = int(sys.argv[4])
    except:
        print '\n usage:'+sys.argv[0]+' jobQuery(in quotes) tableType(0=bkgd, 1=query),' \
                                     +' nJobs(max 500), start(api starting index)'
        print '\n using default values:'
        print '      jobQuery = "" (i.e. generic search)'
        print '     tableType = 0  (i.e. bkgd)'
        print '         nJobs = 1'
        print '         start = 0'
        jobQuery  = ""
        tableType = 0
        nJobs     = 1
        start     = 0
        
    # scan job postings and populate the bkgd tables
    populateTables(jobQuery=jobQuery, tableType=tableType, nJobs=nJobs, start=start)



if __name__ == '__main__':
    main()
