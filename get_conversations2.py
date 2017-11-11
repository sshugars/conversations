import json
import glob
import gzip
from bs4 import BeautifulSoup 
import urllib2


def process_tweet(item):    
    tweetID = item['data-item-id']

    #if tweet has multiple replies...
    try:
        comments = item.findAll('span', {'class' : 'ProfileTweet-actionCount'})
        comment_count = int(comments[0]['data-tweet-stat-count'])

        # ...extract url
        users = item.findAll('a', {'class' : 'account-group js-account-group js-action-profile js-user-profile-link js-nav'})
        user = users[0]['data-user-id']
        new_url = 'http://twitter.com/' + str(user) + '/status/' + str(tweetID)

    except:
        comment_count = 0
        new_url = ""
        print('No comments or URL found for tweet %s' %tweetID)
    
    return tweetID, new_url, comment_count

def get_tweet_ids(url, url_list, tweet_ids):
    
    req = urllib2.Request(url, headers={'User-Agent' : "Magic Browser"}) 
    page_text = urllib2.urlopen( req )
    html = page_text.read()
    soup = BeautifulSoup(html, 'html5lib')

    #add initial tweet ID
    #method 1, from URL
    source = url.split('/')
    source_id = (source[-1])
    source_url = url

    #method 3, from html
    #need to do it this way because of retweets
    for post in soup.findAll('div', {'class': 'permalink-inner permalink-tweet-container'}):
        info = post.findAll('a', {'class': 'tweet-timestamp js-permalink js-nav js-tooltip'})
        
        for item in info:
            source_id = item['data-conversation-id']
            source_url = 'http://twitter.com' + item['href']

    tweet_ids.add(source_id)

    #flag current url as searched
    url_list[url] = True
    url_list[source_url] = True #in case orig url was a retweet

    #now, get all related tweets on this page
    lost_children = set()
    
    # round 1: hidden tweets
    for hidden in soup.findAll('li', {'class': 'ThreadedConversation-moreReplies'}):
        parentID = hidden['data-expansion-url'].split('/')[3]
        lost_children.add(parentID)

    #round 2: threaded tweets
    for post in soup.findAll('div', {'class': 'ThreadedConversation-tweet'}):
        info = post.findAll('li', {'class': 'js-stream-item stream-item stream-item '})
        
        for item in info:            
            tweetID, new_url, comment_count = process_tweet(item)
            tweet_ids.add(tweetID)
            
            search_url = False
            
            if tweetID in lost_children:
                search_url = True
            if comment_count > 1:
                search_url = True
            if new_url in url_list.keys():
                if url_list[new_url] == True:
                    search_url = False
            
            if search_url == True:
                url_list[new_url] = False
            

    # round 3: single tweets
    for post in soup.findAll('li', {'class': 'ThreadedConversation--loneTweet'}):
        
        info = post.findAll('li', {'class': 'js-stream-item stream-item stream-item '})
        
        for item in info:
            tweetID, new_url, comment_count = process_tweet(item)
            tweet_ids.add(tweetID)
            
            search_url = False

            if tweetID in lost_children:
                search_url = True
            if comment_count > 1:
                search_url = True
            if new_url in url_list.keys():
                if url_list[new_url] == True:
                    search_url = False
            
            if search_url == True:
                url_list[new_url] = False
                
    # round 4: strange things
    for post in soup.findAll('div', {'class': 'ThreadedConversation-tweet last'}):
        
        info = post.findAll('li', {'class': 'js-stream-item stream-item stream-item '})
        
        for item in info:  
            tweetID, new_url, comment_count = process_tweet(item)
            tweet_ids.add(tweetID)
            
            search_url = False

            if tweetID in lost_children:
                search_url = True
            if comment_count > 1:
                search_url = True
            if new_url in url_list.keys():
                if url_list[new_url] == True:
                    search_url = False
            
            if search_url == True:
                url_list[new_url] = False
                
    return url_list, tweet_ids




# processed seed tweets
path = '../convo_ids/'
processed = list()
processed_file = 'processed.txt'

#for filename in glob.glob(path + '*.txt'):
#    convoID = filename.split('_')[-1].split('.')[0]
#    processed.append(convoID)

with open(processed_file, 'r') as fp:
    for line in fp.readlines():
        convoID = str(line.strip())
        processed.append(convoID)

print('%s tweets already processed' %len(processed))


# define path
path = '../raw/'
#path = ""
limit = 0

for filename in glob.glob(path + '*.json.gzip'):
    print('Searching file: %s' %filename)

    tweet_urls = list()
    not_found = list()

    #read tweets from source file
    with gzip.open(filename, 'r') as fp:
        try:
            for line in fp.readlines():
                try:
                    tweet = json.loads(line.decode("utf8"))
                    tweetID = tweet['id']

                    if str(tweetID) not in processed:
                        userID = tweet['user']['id']
                        text = tweet['text']
                    
                        if 'trump' in text or 'Trump' in text:
                            url = 'http://twitter.com/' + str(userID) + '/status/' + str(tweetID)
                            tweet_urls.append(url)
                        
                except:
                    pass
                
        except:
            pass
        
    print('%s seed tweets found' %len(tweet_urls))

    # for every tweet in this file
    # recursively get associated tweet_urls and tweet_ids
    for seed_url in tweet_urls:

        progress = tweet_urls.index(seed_url)
        
        if progress%100 == 0:
            remaining = len(tweet_urls) - progress
            print('%s seed tweets left to search' %remaining)

        convoID = seed_url.split('/')[-1]

        with open(processed_file, 'a') as fp:
            fp.write('\n'+convoID)

        tweet_ids = set()
        url_list = dict()

        url_list[seed_url] = False

        count = 1
        url_check = [k for k,v in url_list.items() if v == False]

        while len(url_check) > 0:
            if count%50 == 0:
                print('Unsearched urls: %s\n' %len(url_check))

            count += 1

            try:
                url_list, tweet_ids = get_tweet_ids(url_check[0], url_list, tweet_ids)

            except urllib2.HTTPError:
                print('URL not found:', url_check[0])
                url_list.pop(url_check[0]) #remove from list of urls to check
                not_found.append(url_check[0])

            except:
                raise
            
            #recalculate list of urls to check
            url_check = [k for k,v in url_list.items() if v == False]

        print('Conversation %s tree searched. %s tweets found.' %(convoID, len(tweet_ids)))

        #write identified tweets to file if convo
        if len(tweet_ids) > 4:
            outfile = '../convo_ids/tweet_ids_%s.txt' %convoID

            with open(outfile, 'w') as fp:
                fp.write('\n'.join(list(tweet_ids)))

     
#            if len(not_found) > 0:
#               not_found_file = 'not_found_%s.txt' %seed_id

#               with open(not_found_file, 'w') as fp:
#                   fp.write('\n'.join(not_found))






