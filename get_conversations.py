"""
Retreive conversation trees from a set of seed tweets.

Because Twitter's API does not allow for tracing a full thread, this script uses an html scraper 
to retreive tweetIDs connected to seed tweets. Seed tweets must be stored in one or more .json.gzip
files. For each seed tweet, the script will return a .txt file with the tweetIDs of connected tweets.

Included functions:
    procees_tweet: returns relevant metadata from a connected tweet
    
    get_tweet_ids: gets tweet ids from a given tweet url
    
Input: Folder with .json.gzip objects from Twitter API 
    
Output: A collection of .txt file with tweetIDs for each seed tweet
"""

### Parameters to set ###
raw_path = '../raw/'                # path for input tweets
out_path = '../convo_ids/'          # path for output .txt files
processed_file = 'processed.txt'    # to store list of processed seed tweets, allowing for easy resarting if interupted
min_length = 4                      # record only trees with at least a minimum number of tweets
### End customization ###  


import json
import glob
import gzip
from bs4 import BeautifulSoup 
import urllib.request
import urllib.error


def process_tweet(item, lost_children = set(), url_list = dict()):  
    """
    Parses HTML to get tweetID, url, and comment count for an HTML-defined tweet item
    
    Arguments:
        item : a section of HTML which includes a single tweet's data
        lost_children : a set of tweetIDs which require click-through to see children
        url_list : dict of {url : boolean} object to track urls which need to be searched
    
    Returns:
        tweetID : unique ID of parsed tweet
        url_list : dict of {url : boolean} object to track urls which need to be searched
    """
    
    tweetID = item['data-item-id'] #extract TweetID

    try:
        # get count of comments made responding to this tweet
        comments = item.findAll('span', {'class' : 'ProfileTweet-actionCount'})
        comment_count = int(comments[0]['data-tweet-stat-count'])

        # extract url
        users = item.findAll('a', {'class' : 'account-group js-account-group js-action-profile js-user-profile-link js-nav'})
        user = users[0]['data-user-id']
        new_url = 'http://twitter.com/' + str(user) + '/status/' + str(tweetID)

    except:
        # if comments or url unparsable, return null data for this tweet
        comment_count = 0
        new_url = ""
        print('No comments or URL found for tweet %s' %tweetID)
   
    #decide whether we need to search the URL for this tweet
    search_url = False

    if tweetID in lost_children:    # if this tweet has lost children
        search_url = True
    if comment_count > 1:           # if this tweet has more comments than we can see 
        search_url = True
    if new_url in url_list.keys():  #unless we have already searched this tweet
        if url_list[new_url] == True:
            search_url = False

        # Add this tweet's url to our search queue if it qualifies. 
        if search_url == True:
            url_list[new_url] = False
    
    return tweetID, url_list


def get_tweet_ids(url, url_list, tweet_ids):
    """
    Function called recusively to parse HTML of connected tweets
    
    Arguments:
        url : the url to check on this call
        url_list : dict of {url : boolean} object to track urls which need to be searched
        tweet_ids : set of all tweet_ids found through a seed tweet
    
    Returns:
        url_list : dict of {url : boolean} object to track urls which need to be searched
        tweet_ids : set of all tweet_ids found through a seed tweet
    """
    
    ### Step 1: Make request of url and make the soup ###
    req = urllib.request.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    page_text = urllib.request.urlopen( req )
    html = page_text.read()
    soup = BeautifulSoup(html, 'html5lib')

    ### Step 2: Find current tweetID and mark it as searched ###
    
    # Parse from HTML
    # Do it this way instead of from the URL because 
    # If tweet is retweeted, URL and actual tweet ID will be different 
    for post in soup.findAll('div', {'class': 'permalink-inner permalink-tweet-container'}):
        info = post.findAll('a', {'class': 'tweet-timestamp js-permalink js-nav js-tooltip'})
        
        for item in info:
            source_id = item['data-conversation-id']
            source_url = 'http://twitter.com' + item['href']

    tweet_ids.add(source_id)

    # flag current url as searched
    url_list[source_url] = True 

    ### Step 3: get all related tweets on this page ###
    # Twitter categorizes response tweets into different types, 
    # so we use a few searches to check each category
    
    # Round 1: flag hidden tweets
    # Some threads are cut off with a "more tweets" click through
    # Note parentIDs so we can find their children later
    lost_children = set()
    
    for hidden in soup.findAll('li', {'class': 'ThreadedConversation-moreReplies'}):
        parentID = hidden['data-expansion-url'].split('/')[3]
        lost_children.add(parentID)

    # Round 2: threaded tweets
    for post in soup.findAll('div', {'class': 'ThreadedConversation-tweet'}):
        info = post.findAll('li', {'class': 'js-stream-item stream-item stream-item '})
        
        for item in info:        
            # Call process_tweet to note ID and whether this tweet url needs to be searched
            tweetID, url_list = process_tweet(item, lost_children, url_list)
            tweet_ids.add(tweetID)
            

    # Round 3: single tweets
    for post in soup.findAll('li', {'class': 'ThreadedConversation--loneTweet'}):
        info = post.findAll('li', {'class': 'js-stream-item stream-item stream-item '})
        
        for item in info:
            # Call process_tweet to note ID and whether this tweet url needs to be searched
            tweetID, url_list = process_tweet(item, lost_children, url_list)
            tweet_ids.add(tweetID)
                
    # Round 4: last tweets
    for post in soup.findAll('div', {'class': 'ThreadedConversation-tweet last'}):
        info = post.findAll('li', {'class': 'js-stream-item stream-item stream-item '})
        
        for item in info:  
            # Call process_tweet to note ID and whether this tweet url needs to be searched
            tweetID, url_list = process_tweet(item, lost_children, url_list)
            tweet_ids.add(tweetID)
                
    return url_list, tweet_ids

### Main Function ###

# Step 1: check if we have processed any tweets so far
processed = list()

# Check if we have created a proceed file already
try:
    with open(processed_file, 'r') as fp:
        for line in fp.readlines():
            convoID = str(line.strip())
            processed.append(convoID)
            
# Otherwise, create the file            
except: 
    with open(processed_file, 'w') as fp:
        fp.write("")

print('%s tweets already processed' %len(processed))

# Step 2: iterate through files and search tree for every seed tweet
for filename in glob.glob(path + '*.json.gzip'):
    print('Searching file: %s' %filename)

    # initialize list of seed_urls to search
    tweet_urls = list()

    #read tweets from source file
    with gzip.open(filename, 'r') as fp:
        try:
            for line in fp.readlines():
                try:
                    tweet = json.loads(line.decode("utf8"))
                    tweetID = tweet['id']

                    #check if we have processed this tweet already
                    if str(tweetID) not in processed:  
                        userID = tweet['user']['id']
                        
                        # to condition search on seed tweet text, add:
                        # text = tweet['text']
                        # if "keyword" in text.lower():
                    
                        url = 'http://twitter.com/' + str(userID) + '/status/' + str(tweetID)
                        tweet_urls.append(url)
                except:
                    pass
        except:
            pass
    
    # report # of seed tweets found in this file
    print('%s seed tweets found' %len(tweet_urls))

    # Step 2: for each seed url,
    # Call the recursive function until its conversation tree is searched
    for seed_url in tweet_urls:
        
        # Give periodic updates on progress
        progress = tweet_urls.index(seed_url)
        if progress%100 == 0:
            remaining = len(tweet_urls) - progress
            print('%s seed tweets left to search' %remaining)

        # Define convoID as the ID of the seed tweet
        convoID = seed_url.split('/')[-1]
        
        # Update processed file to note this seed tweet was processed
        # Do this now, otherwise will re-try seed tweets that throw errors if restarted
        with open(processed_file, 'a') as fp:
            fp.write('\n'+convoID)

        tweet_ids = set()  # Set of tweetIDs dound through this seed ID search
        url_list = dict()  # dict of {url : boolean} object to track urls which need to be searched

        url_check = [seed_url] #list of urls which need to be checked, will be updated in recursion

        #recurse while we still have URLs to check
        while len(url_check) > 0:
            try:
                url_list, tweet_ids = get_tweet_ids(url_check[0], url_list, tweet_ids)
            
            # If we can't open the page (eg, tweet deleted)
            # print a message and remove from search list
            except urllib.error.HTTPError:
                print('URL not found:', url_check[0])
                url_list.pop(url_check[0]) #remove from list of urls to check

            # Anything else, raise the error
            except:
                raise
            
            # Recalculate list of urls to check
            url_check = [k for k,v in url_list.items() if v == False]

        print('Conversation %s tree searched. %s tweets found.' %(convoID, len(tweet_ids)))

        # Write identified tweets to file if tree a minimum number of tweets
        if len(tweet_ids) >= min_length:
            outfile = out_path + '_tweet_ids_%s.txt' %convoID

            with open(outfile, 'w') as fp:
                fp.write('\n'.join(list(tweet_ids)))
