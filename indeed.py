#!/usr/bin/env python
"""
indeed.py
Author: Brian Boates

Scrape job postings for a given query from
Indeed.com using the search api for key skills
analysis
"""
import os, sys, re, nltk
import urllib2
import utils
import ghlThreads

def getJobURLs(jobQuery, nURLs=1, start=0):
    """
    return: list of strings (each string is a URL to an
            Indeed.com job posting for "jobQuery")
    params:
            jobQuery: string | search terms for Indeed.com
                      (preprocessed for +'s rather than spaces, etc.)
            nURLs: int | number of job posting URL's to return
            start: int | beginning index for api job search
    """
    # pre-process job query
    jobQuery = jobQuery.strip().lower().replace(' ','+')
    
    # list for all URL's to be stored
    allurls = []
    
    # loop through each page of 20 job postings for jobQuery
    for i in range(nURLs//10+1):
        
        print 'url retrieval =', len(allurls)/float(nURLs)*100.0, 'percent complete'
        
        # api link for 10 postings for jobQuery at a time
        api  = 'http://api.indeed.com/ads/apisearch?publisher=6973678184764538&v=2'
        api += '&q=\"'+jobQuery+'\"&start='+str(start + i*10)
    
        # get the content from api URL
        raw = utils.getURL(api)
        
        # parse the raw data for individual job URL's
        urls = re.findall(r'<url>.*</url>', raw)
        
        # remove the <link> and </link> tags from URL's
        urls = [u.replace('<url>','').replace('</url>','') for u in urls]
        
        # append current page of URL's to list of "all" URL's
        allurls += urls
    
    # return only up to nURLs number of URL's for job postings
    return allurls[:nURLs]


def rssJobURLs(jobQuery, nJobs=10, start=0):
    """
    return: list of strings (each string is a URL to an
            Indeed.com job posting for "jobQuery")
    params:
            jobQuery: string | search terms for Indeed.com
                      (preprocessed for +'s rather than spaces, etc.)
            nJobs: int | number of job postings to return
            start: int | beginning index for api job search
    """
    # pre-process job query
    jobQuery = jobQuery.strip().lower().replace(' ','+')
    
    # list for all URL's to be stored
    allurls = []
    
    # loop through each page of 20 job postings for jobQuery
    for i in range(nJobs//20+1):
        
        print 'url retrieval =', len(allurls)/float(nJobs)*100.0, 'percent complete'
        
        # rss link for first 10 postings for jobQuery
        rss = 'http://rss.indeed.com/rss?q='+jobQuery+'&start='+str(i*20)
        
        # get the content from rss URL
        raw = utils.getURL(rss)
        
        # parse the raw data for individual job URL's
        urls = re.findall(r'<link>.*</link>', raw)[2:] # skip first two links
        
        # remove the <link> and </link> tages from URL's
        urls = [u.replace('<link>','').replace('</link>','') for u in urls]
        
        # append current page of URL's to list of "all" URL's
        allurls += urls
        
    # return only up to nJobs number of URL's for job postings
    return allurls[:nJobs]


def jdClean(jd):
    """
    return: processed/cleaned job description
    params:
        jd: string | a string containing an entire "J"ob "D"escription
        
    this function does all of the gritty punctuation and common word removal
    or at least a large portion of it
    """
    # remove remnant mark-up
    jd = re.sub(r'<\w+>', ' ', jd)
    jd = re.sub(r'</\w+>', ' ', jd)
    jd = re.sub(r'<\w+/>', ' ', jd)
    
    # prevent stranded t's and s's from words like don't and client's
    jd = re.sub(r"'\w\s", ' ', jd)
    
    # remove weird apostrophe characters
    jd = re.sub('\\xe2\\x80\\x99\w', '', jd)
    
    # find all occurences of ' wordPUNCTUATIONword ' to "fix"
    fix = re.findall(r'\s\w+[^\w\s]\w+\s', jd)
    for term in fix:
        punc = re.search(r'[^\w\s]', term).group()
        if punc == '/' or punc == ',':
            # replace "/" or "," with an "and"
            jd = jd.replace(punc,' and ')
        else:
            jd = jd.replace(term, term.replace(punc,''))
         
    # convert unwanted punctuation into spaces (keep +'s)
    jd = re.sub('[^A-Za-z0-9\s\+\#-]+', ' ', jd)
    
    # remove all upper-case letters
    jd = jd.lower()
    
    # remove pure numbers
    jd = re.sub(r'\s\d+\s', ' ', jd)
    
    # remove pure puncuations
    jd = re.sub(r'\s[\+\#-]+\s', ' ', jd)
    
    # only keep one-letter words that are C or R
    Nr = jd.split().count('r')
    Nc = jd.split().count('c')    
    fix = re.findall(r'\w\w+', jd)
    jdnew = ''
    for f in fix: jdnew += f+' '
    for i in range(Nr): jdnew += 'r '
    for i in range(Nc): jdnew += 'c '
    jd = jdnew
#    jd = re.sub(r'\s[^CR]\s',' ', jd)
    
    # fix "html css" bigrams / get rid of them
    jd = re.sub(r'html\s+css','html and css', jd)
    
    # remaining hacks
    jd = jd.replace('objectoriented','object oriented')
    jd = jd.replace('java script','javascript')
    jd = jd.replace(' js ',' javascript ')
    jd = jd.replace('css3','css')
    
    return jd


def parseJobPosting(url):
    """
    return: jobkey[string] position[string], company[string], location[string],
                                                              words[list of strings]
    params:
            url: string | url for the job posting to parse
    """
    # extract raw data from URL and remove returns
    raw = utils.getURL(url)
    raw = raw.replace('\n',' ')
    
    # retrieve the jobkey from the url
    jobkey = re.search(r'jk=\w+&amp', url).group().replace('jk=','').replace('&amp','')
    
    # extract job position
    try:
        position = re.search(r'<title>.*</title>', raw).group()
        # position = re.search(r'>\w.*\-.*\-.*\|', position).group()
        position = re.search(r'>\w.*\-.*\|', position).group()
        position = position.replace('>','').replace('|','').split('-')[0].replace('job','').strip()
    except AttributeError:
        position = 'Unknown'
        
    # retrieve job location
    try:
        location = re.search(r'<span class="location">.*?<span class="summary">', raw).group()
        location = re.search(r'<span class="location">.*?</span>', location).group()
        location = location.replace('<span class="location">','').replace('</span>','')
    except AttributeError:
        location = 'Unknown'
    
    # receive job's company
    try:
        company = re.search(r'<span class="company">.*?<span class="summary">', raw).group()
        company = company.split('</span>')[0].split('>')[-1]
    except AttributeError:
        company = 'Unknown'
    
    # retrieve the job description section
    try:
        start = 'span class="summary"'
        end = 'days ago'
        end   = '<span class="sdn">'#+company
        #jd = re.search(r''+start+'.*'+end+'.*'+'days ago', raw,re.IGNORECASE).group()
        jd = re.search(r''+start+'.*?'+end, raw).group()
        jd = jd.replace('span class="summary"','').replace('<span class="sdn">','')
        jd = jd.replace('<span class="date">',' ').replace('days ago',' ')
    except AttributeError:
        jd = ''
    
    # more advanced processing/cleaning of the job description
    words = jdClean(jd).split() # list of words
    
    return jobkey, position, company, location, words


def getTerms(words, commonwords, keywords, threshold=100, magnify=1.0):
    """
    return: dictionary of all unique terms and the number of
            times they appeared in the posting (limited by threshold)
    params:
            words: list[string] | list of words as strings
            commonwords: list[string] | list of common words to ignore
            keywords: list[string] | list of keywords to possibly magnify
            threshold: int | threshold for counts (i.e. if a term appears more 
                       than threshold times, it won't be kept; default=100)
            magnify: float | value to scale keywords counts by (default=1.0 
                     i.e. no scaling)
    """
    # consider bigrams and trigrams
    bigrams, trigrams = [], []
#    bigrams  = utils.getNgrams(words, N=2)
#    trigrams = utils.getNgrams(words, N=3)
    
    # simplify the words list by removing common words
    # words = removeCommonWords(words)
    
    # make list of all terms (including N-grams)
    allterms = words + bigrams + trigrams
    
    # initialize terms dictionary
    terms = {}
    
    # loop over allterms
    for term in allterms:
        
        # if key is a keyword
        weight = 1.0
        if term in keywords:
            # magnify its importance
            weight = magnify
            
        # retrieve count for current term        
        c = allterms.count(term)
        
        # only add a count for terms appearing less
        # than threshold and not in commonwords
        if c <= threshold and term not in commonwords:
            terms[term] = weight
        
    return terms


def joinTermsDicts(td1, td2, magnify=1.0):
    """
    return: joined terms dictionary with accumulated counts
    params:
            td1: dict | first dictionary of terms (already free of common words)
            td2: dict | first dictionary of terms (already free of common words)
            keywords: list[string] | list of keywords to magnify importance
            magnify: float | factor to multiply occurences of keywords by
                     (default=10.0)
    """
    # make sure td2 is the shorter dictionary
#    if len(td1) < len(td2) and td1 != {}: td1, td2 = td2, td1
    
    # loop over terms in td2 and add to td1
    for key, value in td2.iteritems():
        
            # check if key already in td1, simply add to the count
            if key in td1.keys():
                td1[key] += td2[key]
        
            # else, add a new key to td1
            else: td1[key] = td2[key]
        
    return td1


def _performQuery(jobQuery, nJobs=10, nReturn=20, thresh=2, mag=1.0):
    """
    return: list[string] | list of N top skills with their rank
    params:
        jobQuery: string | query for job search
        nJobs: int | number of job postings to use in skill search (default=10)
        nReturn: int | number of skills to return (default=20)
        thresh: int | threshold for discounting frequently occuring words
        mag: float | scaling factor for keywords if requested
    """
    # pre-process job query
    jobQuery = jobQuery.strip().lower().replace(' ','+')
    
    # get list of keywords for magnification
    keywords = utils.readKeywords(fname='keywords.txt')
    
    # get list of "common" words for removal
    commonwords = utils.readCommonWords(fname='commonwords.txt') + jobQuery.replace('+',' ').split()
    
    # retrieve list of URL's for jobQuery
    urls = getJobURLs(jobQuery, nJobs=nJobs)
    
    # create dict and list to hold ALL terms and words from ALL URL's
    terms, allwords = {}, []
    
    # loop over all job posting URL's
    for url in urls:
        
        # retrieve information from URL's job posting
        jobkey, position, company, location, words = parseJobPosting(url)
        
        # print useful info to screen
        print urls.index(url), #url,        
        print '# position:',position,'# company:',company,'# location:',location
        
        # make terms dictionary including desired N-grams
        # limited by count threshold and/or with keywords magnified
        terms = joinTermsDicts(terms, getTerms(words, commonwords, keywords, 
                                               threshold=thresh, magnify=mag) )
        
        # append new set of words to the allwords list for Ngram analysis
        allwords += words
            
    # sort the terms by their (possibly magnified) occurence
    results = []
    for key, value in sorted(terms.iteritems(), key=lambda (k,v): (v,k)):
         results.append( (key,str(int(value))) )
    
    # bigram collocations
#    text = nltk.Text(allwords)
#    print text.collocations(num=20)
    
#    jaccard = {}
#    for word in set(allwords):
#        jaccard[word] = utils.jaccard([word], allwords)
#    jresults = []
#    for key, value in sorted(jaccard.iteritems(), key=lambda (k,v): (v,k)):
#         jresults.append( (key, str( value )) )
    
    # trim results down to requested amount and reverse
    results = results[-nReturn:][::-1]
#    results = jresults[-nReturn:][::-1]
#    results = jresults[::-1]
    
#    return results
    
    return allwords

