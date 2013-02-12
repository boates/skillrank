#!/usr/bin/env python
"""
routes.py
Author: Brian Boates

Flask based script for Skill Rank web-app
"""
from flask import Flask, render_template
from flask import request, jsonify
import MySQLdb as mdb
from analysis import getResults

# create new instance of Flask class
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/analyze', methods=['POST'] )
def findSkills():
    
    # get jobQuery and start
    jobQuery = request.form['jobQuery']
    start    = int(request.form['start'])
    
    # set nJobs to 50 ---> good balance of quality/speed
    nJobs = 50
    
    # set number of bubbles for d3 visualization
    nBubbles = 30
    
    # get the results as list[tuple(term,relevance,count)]
    results, biResults = getResults(jobQuery=jobQuery, nJobs=nJobs, start=start)
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
         
    # return in jsonified format
    return jsonify(dictResults)


@app.route('/search', methods=['GET', 'POST'])
def search():
    
    # if the search bar is being used
    if request.method == 'POST':
        
        # get jobQuery, nJobs, and start
        jobQuery = request.form['query']
        nJobs    = int(request.form['njobs'])
        start    = int(request.form['start'])
        
        # prepare the results header
        nJobsString = 'Key skills based on '+str(nJobs)+' job postings for \"'+jobQuery+'\"'
        
        results = getResults(jobQuery, nJobs, start)
        
        # render the template with the results
        return render_template('search.html', results=results, nJobsString=nJobsString,
                                              th=("Skill","Relevance","Occurence"))
                                              
    # otherwise just return home.html
    return render_template('search.html', th=('','',''))


@app.route('/empty', methods=['GET', 'POST'])
def empty():
    return render_template('empty.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/data')
def data():
    return render_template('data.html')


@app.route('/source')
def source():
    return render_template('source.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')




if __name__ == '__main__':
    app.run(debug=True)
#    app.run('0.0.0.0', port=8080)
