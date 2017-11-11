import json
import glob
import gzip
from random import choice

def get_threads(tweets):
    threads = list()
    thread = list()
    parents = dict()

    orphans = [k for k in tweets.keys()]

    #find root and parents
    for tweetID in orphans:
        parentID = tweets[tweetID]['in_reply_to_status_id_str']
        
        if parentID == None:
            thread.append(tweetID)
        
        parents.setdefault(parentID, list()) #parent can have more than one child
        parents[parentID].append(tweetID)
     
    try:
        root = thread[0]    
        orphans.remove(root)
    except:
        pass

    threads.append(thread)
    
    # construct threads 
    max_iter = len(orphans) * 2
    itr_count = 0
    
    while len(orphans) > 0 and itr_count < max_iter and len(thread) > 0:
        itr_count += 1
            
        for thread in threads:
            parent = thread[-1]
            
            try:
                children = parents[parent]
                
                if len(children) > 1: #if more than one child
                    for child in children[1:]:
                        new_thread = [t for t in thread]
                        new_thread.append(child)
                        threads.append(new_thread)

                        orphans.remove(child)
                
                thread.append(children[0])
                orphans.remove(children[0])
                
            except:
                pass

    #throw out short convos
    if max([len(thread) for thread in threads]) < 3:
        threads = list()

    #throw out convo if we there are too many orphans
    if float(len(orphans)) / len(tweets) > 0.1:
        print('percent orphaned:', float(len(orphans)) / len(tweets) )
        # print(orphans)
        threads = list()  

    return threads


path ='tweets/'

convos = dict()

for filename in glob.glob(path + '*.json.gzip'):
    fileID = filename.split('.')[0].split('_')[-1]

    with gzip.open(filename, 'r') as fp:
        for line in fp.readlines():          
            tweets = json.loads(line.decode("utf8"))
            
            if len(tweets) > 2:
                print(filename, len(tweets))
                convos[fileID] = tweets

selected = dict()

for convoID, tweets in convos.items():
    threads = get_threads(tweets)

    print(convoID, len(threads))
    
    if len(threads) > 0:
        selected[convoID] = dict()
        selected[convoID]['threads'] = threads

        selected[convoID]['tweets'] = dict()

        for tweetID in tweets:
            selected[convoID]['tweets'][tweetID] = tweets[tweetID]

print(len(selected), 'conversations found')

with gzip.open('conversations.json.gzip', 'w') as fp:
    print >> fp, json.dumps(selected)