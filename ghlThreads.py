#!/user/bin/env python
"""
threading.py
Author: George H. Lewis
Modified by: Brian Boates

Use threading to speed up squential URL pulls

original source:
https://gist.github.com/ghl3/4556336
"""
import threading
from Queue import Queue
import indeed
 
class getIndeed(threading.Thread):
    """
    A class to download indeed job postings
    from a shared queue using threads for
    boosted efficiency
    """
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self._stop = threading.Event()
        self.articles = []
        self.queue = queue
    
    def getArticles(self):
        return self.articles
    
    def run(self):
        while True:
            if self.queue.empty(): 
                return
            url = self.queue.get()
            returnItems = indeed.parseJobPosting(url)
            self.articles.append(returnItems)


def threadResults(urls, num_threads=8):
    """
    Download content from all urls, return list of 
    indeed.parseJobPosting return tuples
    i.e. [(jobkey, position, company, location, words), ...]
    """
    q = Queue()
    for url in urls:
        q.put(url)
    
    # start threads to consume the queue
    threads = [] 
    for i in xrange(num_threads):
        thread = getIndeed(q)
        thread.start()
        threads.append(thread)
    
    # collect results from threads
    for thread in threads:
        thread.join()
 
    # gather and return all results
    documents = []
    for thread in threads:
        documents += thread.getArticles()
    return documents

