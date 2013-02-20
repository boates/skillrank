#!/usr/bin/env python
"""
routes.py
Author: Brian Boates

Flask based script for Skill Rank web-app
"""
from flask import Flask, render_template
from flask import request, jsonify
from collections import OrderedDict
from analysis import getResults

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/search')
def search():
    return render_template('search.html')


@app.route('/search/<query>')
def searchTo(query):
    query = query.replace('+',' ')
    return render_template('search.html', query=query)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/data')
def data():
    return render_template('data.html')


@app.route('/source')
def source():
    return render_template('source.html')


@app.route('/demo')
def demo():
    return render_template('demo.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


# dictionary for cached job queries
cache = OrderedDict()
cacheLimit = 1000

@app.route('/analyze', methods=['POST'] )
def runAnalysis():
    
    # get jobQuery and start
    jobQuery = request.form['jobQuery']
    
    # check to see if jobQuery already in cache
    if jobQuery in cache:
        print 'using cache brosef'
        return jsonify(cache[jobQuery])
    
    # set nJobs to 50 ---> good balance of quality/speed
    nJobs = 50
    
    # start from the first indeed.com API results
    start = 0
    
    # set number of bubbles for d3 visualization
    nBubbles = 25
    
    # get the results as list[tuple(term,relevance,count)]
    results, biResults, resultsString = getResults(jobQuery=jobQuery, nJobs=nJobs, start=start)
    
    # catch for case with no results
    if resultsString == '':
        resultsString = 'No results found for "'+jobQuery+'"'
        return jsonify({'resultsString':resultsString})
    
    results += biResults
    
    # sort the list in the most horrible way imaginable
    # but it's short so it's okay :)
    counts = [int(r[2]) for r in results] # create list of all counts
    newResults = []
    while counts:
        # find the max count index, then remove it
        maxC = counts.index(max(counts))
        # put the max count result in newResults
        newResults.append(results[maxC])
        # pop the result out of both lists to keep in sync
        counts.pop(maxC)
        results.pop(maxC)
        
    # filter single letters R and C if at top
    # more likely a bug than reality
    if newResults[0][0]+newResults[1][0] in ['cr','rc']:
        newResults = newResults[2:]
        
    # update results to newResults
    results = newResults[:nBubbles]
    
    # if results is an empty list
    if not results:
        # return empty jsonify dict
        return jsonify({})
        
    # build the results dictionary for d3
    dictResults = {'items':[]}
    
    # put words and bigrams in the results dictionary
    for term, relevance, count in results:
            dictResults['items'].append({'term':term, 'relevance':relevance,
                                         'count':float(count), 'len':len(term.split())})
                                         
    # add the jobQuery to the results dictonary for quick reference
    dictResults['query'] = str(jobQuery).replace(' ','+')
    
    # add the resultsString to the results dictionary
    dictResults['resultsString'] = resultsString
                                         
    # add results to the cache (keep length below 1000)
    if len(cache) > cacheLimit:
        cache.popitem(last=False)
    cache[jobQuery] = dictResults
    
    # return in jsonified format
    return jsonify(dictResults)


if __name__ == '__main__':
    app.run(debug=True)
#    app.run('0.0.0.0', port=8080)
