"""
Process tweet metadata into single document indexed by conversation ID.

Filter out conversations with missing tweets

Included functions:
    get_threds: returns list of list with ordered tweetIDs

Input:
    Folder of .json.gzip files where each file contains metadata for tweets in the same conversation tree

Output:
    conversation.json.gzip: a single file with all conversation data. Formated as:

    convoID : { 
            tweets : { tweetID: tweet metadata}
            threads: [[tweetIDs ordered by entry]]        
                }
"""

### Parameters to set ###
path = '../conversations/'              #folder of .json.gzip files with tweet metadata
outfile = 'conversations.json.gzip'     #output file of tweet metadata and threads
### End customization ###  

import json
import glob
import gzip



def get_threads(tweets):
    """
    Creates a list of list of threads (ordered tweets) within a conversation tree

    Arguments:
        tweets : JSON / dictionary format of metadata for tweets from a single conversation tree

    Returns:
        threads : list of list of ordered tweetIDs
    
    """

    threads = list() #to store all threads
    
    thread = list() #to store current thread
    parents = dict() #dict of form {ParentID : [childIDs]}  

    orphans = [k for k in tweets.keys()] #all IDs start as orphans

    #find root and parents
    for tweetID in orphans:
        parentID = tweets[tweetID]['in_reply_to_status_id_str']
        
        parents.setdefault(parentID, list()) #parent can have more than one child
        parents[parentID].append(tweetID)
        
    # find root
    if len(parents[None]) > 1:
        counts = [(len(parents[possible]), possible) for possible in parents[None] if possible in parents]
        
        root = sorted(counts)[0][1]
    else:
        root = parents[None][0]


    orphans.remove(root)
        
    thread.append(root)

    threads.append(thread)
    
    # construct threads 
    #include max_iter attempts since deleted tweets (missing metadata) 
    #will result in threads which can't be reconstructed
    max_iter = len(orphans) * 2 
    itr_count = 0

    while len(orphans) > 0 and itr_count < max_iter and len(thread) > 0:
        itr_count += 1
            
        #for every thread of the conversation...
        for thread in threads:
            parent = thread[-1]  #find currently final tweetID. 
            
            #if this tweet is a parent, we want to expand the thread(s) with its child(ren)
            try:
                children = parents[parent]
                
                if len(children) > 1: #if more than one child
                    for child in children[1:]:
                        new_thread = [t for t in thread] #duplicate current thread 
                        new_thread.append(child) #add child to new thread
                        threads.append(new_thread)

                        orphans.remove(child)
                
                thread.append(children[0]) #add child to thread
                orphans.remove(children[0]) 
                
            except:
                pass

    #throw out short convos
    if max([len(thread) for thread in threads]) < 3:
        threads = list()

    #throw out convo if we there are too many orphans
    percent_orphaned = float(len(orphans)) / len(tweets)
    if percent_orphaned > 0:  
        threads = list()  

    return threads


### Main Function ###
convos = dict()

for filename in glob.glob(path + '*.json.gzip'):
    fileID = filename.split('_')[-1].split('.')[0]  #fileID will be used as convoID

    #each file contains tweet metadata for a single converation
    with gzip.open(filename, 'r') as fp:
        for line in fp.readlines():          
            tweets = json.loads(line.decode("utf8"))

            #ignore conversations with less than 2 tweets
            if len(tweets) > 2:
                convos[fileID] = tweets

print('%s total convos' %len(convos))

selected = dict()

for convoID, tweets in convos.items():
    threads = get_threads(tweets)
    
    if len(threads) > 0:
        selected[convoID] = dict()
        selected[convoID]['threads'] = threads

        selected[convoID]['tweets'] = dict()

        for tweetID in tweets:
            selected[convoID]['tweets'][tweetID] = tweets[tweetID]

print('%s complete conversations found' %len(selected))

with gzip.open(outfile, 'w') as fp:
    print >> fp, json.dumps(selected)