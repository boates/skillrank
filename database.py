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
import indeed

def dbRemove(db='skillrank'):
    """
    WARNING! This function will drop current skillrank database
    params:
            db: string | the name of the MySQL database
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
    params:
            db: string | the name of the MySQL database
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
        
        # create bkgd_jobkeys table: id (primary key) | jobkey
        # indeed.com jobkeys are 16 characters long
        cur.execute("CREATE TABLE IF NOT EXISTS \
                     bkgd_jobkeys(id INT PRIMARY KEY AUTO_INCREMENT, \
                                  jobkey CHAR(16))")
                              
        # create bkgd_words table: id (primary key) | term | count
        cur.execute("CREATE TABLE IF NOT EXISTS \
                     bkgd_words(id INT PRIMARY KEY AUTO_INCREMENT, \
                                term VARCHAR(64), count INT)")
        
    # close cursor to skillrank database
    if cur: cur.close()
    
    # close connection to skillrank database
    if con: con.close()


def newJobkey(cur, jobkey):
    """
    Return True/False if jobkey is new/already in table
    params:
           cur: cursor to skillrank database
        jobkey: string | indeed.com unique job posting ID
    """
    # jobkeys table
    jTable = 'bkgd_jobkeys'
        
    # check to see if jobkey exists
    cur.execute("SELECT * FROM "+jTable+" WHERE jobkey = \'"+jobkey+"\'")
    
    # True if jobkey is new, False if already present
    new = not cur.fetchone()
    
    return new


def updateTermCount(cur, term, table='bkgd_words'):
    """
    Update the count for a term in a given table
    or initialize to 1 if not already present
    return: 0 if table update was successful
    params:
            cur: cursor to skillrank database
          table: skillrank db table to use
           term: term to update in skillrank database
    """
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
        
    return 0


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


def insertPosting(cur, jobkey, words):
    """
    Insert words, bigrams, and trigrams from a single job posting
    into their respective tables
    return: True if jobkey is new
            False if jobkey is not new
    params:
            cur: cursor to skillrank database
         jobkey: string | indeed.com unique job posting ID
          words: list[string] list of words from a single job posting
    """
    # bkgd tables
    jTable = 'bkgd_jobkeys'
    wTable = 'bkgd_words'
    
    # check to see if jobkey is new
    if newJobkey(cur, jobkey):
        
        # if new, insert jobkey into jobkeys table
        cur.execute("INSERT INTO "+jTable+"(jobkey) VALUES(\'"+jobkey+"\')")
        
        # update word counts
        for word in words:
            val = updateTermCount(cur=cur, term=word, table=wTable)
            
        # return true if jobkey is new and insertion was performed
        return True
    
    # if jobkey is not new, ignore the posting and return false
    else:
        return False


def populateTables(jobQuery, nJobs=1, start=0):
    """
    Populate tables with words from job postings
    return: 
    params:
         jobQuery: string | job query
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
                val = insertPosting(cur, jobkey, words)
                
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
        nJobs     = int(sys.argv[3])
        start     = int(sys.argv[4])
    except:
        print '\n usage:'+sys.argv[0]+' jobQuery(in quotes), nJobs(max 500),' \
                                     +' start(api starting index)'
        print '\n using default values:'
        print '      jobQuery = "" (i.e. generic search)'
        print '         nJobs = 1'
        print '         start = 0'
        jobQuery  = ""
        nJobs     = 1
        start     = 0
        
    # scan job postings and populate the bkgd tables
    populateTables(jobQuery=jobQuery, nJobs=nJobs, start=start)


if __name__ == '__main__':
    main()
