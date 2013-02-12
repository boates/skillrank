#!/usr/bin/env python
"""
utils.py
Author: Brian Boates

Python script containing utility functions 
for the skillrank package
"""
import os, sys, re
import urllib2
import nltk

def getURL(url):
    """
    return: raw text from URL as a string
    params:
            url: string | url to retrieve data from
    """
    return urllib2.urlopen(url).read()


def isWord(word):
    """
    return: True if word is an english word, False otherwise
    params:
            word: string | word to check
    """
    if nltk.corpus.wordnet.synsets( word ):
        return True
    else: return False


def isPlural(word1, word2):
    """
    Compare two words to see if one is the plural of another
    (limited to pluralities ending in "s")
    
    return: True/False
    params:
            word1: string | to be compared with word2
            word2: string | to be compared with word2
    """
    # if neither word ends in "s", return false
    if word1[-1] != 's' and word2[-1] != 's':
        return False
    # otherwise check word1/word2 for 's'-removed similarity
    return word2[:-1] == word1 or word1[:-1] == word2


def inTerm(word1, word2):
    """
    Compare two words to see if one is inside the other
    
    return: True/False
    params:
            word1: string | to be compared with word2
            word2: string | to be compared with word2
    """
    return word1 in word2 or word2 in word1


def getNgrams(strings, N=2):
    """
    return: list of strings of N-grams (e.g. bigrams, trigrams, etc.)
    params:
        strings: list of strings to make the N-grams from
        N: int | the N in N-gram (default = 2 for bigram)
    """
    # initiate list for N-grams
    grams = []
    
    # loop over all words in strings
    for i in range(len(strings)-N):
        
        # make the N-gram
        gram = strings[i]
        for j in range(N-1):
            gram += ' '+strings[i+j+1]
        
        # store the N-gram
        grams.append(gram)
    
    return grams


def rankedBigrams(words):
    """
    return: list of ranked bigrams as [((word1, word2), rank), ...]
    params:
            words: list[string] | list of words
    """
    bam     = nltk.collocations.BigramAssocMeasures()
    bigrams = nltk.collocations.BigramCollocationFinder.from_words(words)
    return bigrams.score_ngrams(bam.likelihood_ratio)


def rankedTrigrams(words):
    """
    return: list of ranked trigrams as [((word1, word2, word3), rank), ...]
    params:
            words: list[string] | list of words
    """
    tam      = nltk.collocations.TrigramAssocMeasures()
    trigrams = nltk.collocations.TrigramCollocationFinder.from_words(words)
    return trigrams.score_ngrams(tam.likelihood_ratio)


def getBigrams(words, num=100):
    """
    return: list[tuple(string, string)]
    params:
            words: list[string] | list of words as strings
            num: int | number of bigrams to return (default=100)
    """
    from StringIO import StringIO
    
    # create nltk.text object
    text = nltk.Text(words)
    
    # redirect stdout to StringIO()
    actual_stdout = sys.stdout
    sys.stdout = StringIO()
    
    # get the collocations (bigrams)
    text.collocations(num=num)
    
    # redirect stdout back to original
    sys.stdout = actual_stdout
    
    # process the bigrams a little bit
    bigrams = [c[0]+' '+c[1] for c in text._collocations]
    
    return bigrams


def readKeywords(fname='keywords.txt'):
    """
    return: list of keywords from keywords.txt
    params:
            fname: string | filename with stored keywords
    """
    # open keywords file
    f = open(fname, 'rU')
    
    # loop over lines in file and create keywords list
    keywords = []
    for line in f:
        
        # clean the keywords as you would the job description
        line = re.sub('[^A-Za-z0-9\s\+-]+', ' ', line).lower().strip()
        
        # append line to keywords
        keywords.append(line)
        
        # include extra entries for hyphenated terms
        if '-' in line:
            keywords.append(line.replace('-',' '))
            
    return keywords    


def readCommonWords(fname='commonwords.txt'):
    """
    return: list of "common" words as strings
    params:
            fname: string | filename with stored common words
    """
    # open commonwords file
    f = open(fname, 'rU')
    
    # loop over lines in file and create commonwords list
    commonwords = []
    for line in f:
        
        # clean the commonwords as you would the job description
        line = re.sub('[^A-Za-z0-9\s\+-]+', ' ', line).lower().strip()
        
        # append line to commonwords
        commonwords.append(line)
        
    return commonwords


def removeCommonWords(words):
    """
    return: modified "words" list where the pre-determined
            "common" words have been removed
    params:
            words: list[string] | original list of words
    """
    # common words list
    commons = readCommonWords()
    
    # loop over words list and only keep "uncommon" words
    new = []
    for word in words:
        if word not in commons: new.append(word)
        
    return new


def union(A, B):
    """
    return: A U B
    params:
            A: list[x] | a list of items
            B: list[x] | a list of items (not unique)
    """
    return A + B


def intersection(A, B):
    """
    return: A intersect B
    params:
            A: list[x] | a list of items
            B: list[x] | a list of items (not unique)
    """
    return [t for t in A if t in B]


def jaccard(A, B):
    """
    return: jaccard distance J(A,B)
            J(A,B) = 1 - |A intersect B| ) / |A U B|
    params:
            A: list[x] | a list of items
            B: list[x] | a list of items (not unique)
    """
#    return 1 - len( intersection(A,B) ) / float( len( union(A,B) ) )
    return 1 - B.count(A[0]) / float( len( union(A,B) ) )

