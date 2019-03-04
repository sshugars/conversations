"""
Calculate features for tweets / conversations
 
Input:
   .json.gzip file of tweet metadata data. Expected to be of format:
       convoID : { 
            tweets : { tweetID: tweet metadata}
            threads: [[tweetIDs ordered by entry]]        
                }

    .json.gzip file with topic loadings for each tweetID of format:
        {convoID : 
             {tweetID : {topic loadings}}}          

Output: 
    .txt.gzip file with matrix of output features
"""

### Parameters to set ###
path = '/Users/Shugars/iPython Notebooks/Conversation patterns/'        #set path
topic_file = 'topic_file2.json.gzip'                                #input topic file
con_file = 'conversations.json.gzip'                                    #input conversation file
feature_file = 'conv_features_v6.txt.gzip'                              #output features matrix
valence_file = 'BRM-emot-submit.csv'                                   #word list for valence calculations
### End customization ###  

import json
import gzip
from afinn import Afinn
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np
from scipy import spatial as spatial
from datetime import datetime

#set up
#build valence dictionary
sentiment = dict()

with open(path + valence_file, 'r') as fp:
    for line in fp.readlines():
        line = line.strip().split(',')
        if line[2] != 'V.Mean.Sum':
            word = line[1]
            valence =  float(line[2])
            arousal = float(line[5])
            dominance = float(line[8])
            
            sentiment.setdefault(word, dict())
            sentiment[word]['valence'] = valence - 5.06 		#subtract mean 
            sentiment[word]['arousal'] = arousal - 4.21			#subtract mean
            sentiment[word]['dominance'] = dominance - 5.18		#subtract mean

# calculate valence scores
def get_valence(text, sentiment):
  
    valence = 0.
    arousal = 0.
    dominance = 0.
    
    for word in text.split(' '):
        if word in sentiment:
            valence += sentiment[word]['valence']
            arousal += sentiment[word]['arousal']
            dominance += sentiment[word]['dominance']
    
    valence_scores = dict()
    valence_scores['valence'] =  float("{0:.2f}".format(valence))
    valence_scores['arousal'] = float("{0:.2f}".format(arousal))
    valence_scores['dominance'] = float("{0:.2f}".format(dominance))
    
    return valence_scores

#convert string post_time to datetime object
def get_timestamp(post_time, month_dict):
    post_time = tweets[tweetID]['created_at'].split()

    hour, minute, second = map(int, post_time[3].split(':'))
    timestamp = datetime(year = int(post_time[5]), month = month_dict[post_time[1]], day = int(post_time[2]), 
                         hour = hour, minute = minute, second = second)
    
    return timestamp


# calculate features for a collection of tweets
def get_tweet_features(tweets, parents, topics, j):
    afinn = Afinn()
    analyzer = SentimentIntensityAnalyzer()
    
    tweet_features = dict()

    for tweetID in tweets:
        tweet_features.setdefault(tweetID, dict())
        
        #### Tweet features ####
        
        # step 1: easy stuff
        tweet_features[tweetID]['favorite_count'] = tweets[tweetID]['favorite_count']
        retweets = tweets[tweetID]['retweet_count']
        tweet_features[tweetID]['retweet_count'] = retweets      

        #calculate `quality' tweets with no replies get quality == 0
        if tweetID in parents:
            replies = len(parents[tweetID])
            quality = float(retweets) / replies
        else: 
            replies = 0
            quality = 0
            
        tweet_features[tweetID]['reply count'] = replies
        tweet_features[tweetID]['quality'] = quality
        
        # step 2: medium stuff
        # source device for post:
            # 0 = iPhone
            # 1 = Android
            # 2 = Web
            # 3 = Other (media studio, tweet deck, etc)
        source = tweets[tweetID]['source']

        if 'iPhone' in source:
            tweet_features[tweetID]['source'] = 0
        elif 'Android' in source:
            tweet_features[tweetID]['source'] = 1
        elif 'Web' in source:
            tweet_features[tweetID]['source'] = 2  
        else:
            tweet_features[tweetID]['source'] = 3

        # post time
        post_time = tweets[tweetID]['created_at'].split()

        # code day of the week
        if post_time[0] == 'Mon':
            day = 0
        elif post_time[0] == 'Tue':
            day = 1
        elif post_time[0] == 'Wed':
            day = 2
        elif post_time[0] == 'Thu':
            day = 3
        elif post_time[0] == 'Fri':
            day = 4
        elif post_time[0] == 'Sat':
            day = 5
        elif post_time[0] == 'Sun':
            day = 6
        else:
            day = -1
            print('No day of the week for tweet %s' %tweetID)
            
        #transform to cyclical variable
        tweet_features[tweetID]['xday'] = np.sin(2*np.pi*day/7)
        tweet_features[tweetID]['yday'] = np.cos(2*np.pi*day/7)

        #get hour in GMT
        tweet_features[tweetID]['hour'] = post_time[3].split(':')[0]  
        hour = int(post_time[3].split(':')[0])
        #transform to cyclical
        tweet_features[tweetID]['xhour'] = np.sin(2*np.pi*hour/24)
        tweet_features[tweetID]['yhour'] = np.cos(2*np.pi*hour/24)
        
        #step 3: hard stuff
        text = tweets[tweetID]['full_text'] 

        #character count
        tweet_features[tweetID]['chars'] = len(text)

        #count mentions
        mentions = [c for c in text if c == '@']
        tweet_features[tweetID]['mentions'] = len(mentions)

        #code url
        #No url = 0, includes url = 1
        url_check = tweets[tweetID]['entities']['urls']

        if len(url_check) > 0:
            tweet_features[tweetID]['url'] = 1
        else:
            tweet_features[tweetID]['url'] = 0

        #count hashtags
        hashtag_check = tweets[tweetID]['entities']['hashtags']

        tweet_features[tweetID]['hashtags'] = len(hashtag_check)
        
        # sentiment afinn
        score = afinn.score(text)
        tweet_features[tweetID]['sentiment'] = score
        
        # sentiment Vader
        vs = analyzer.polarity_scores(text)
        tweet_features[tweetID]['vader_neg'] = vs['neg']
        tweet_features[tweetID]['vader_neu'] = vs['neu']
        tweet_features[tweetID]['vader_pos'] = vs['pos']
        tweet_features[tweetID]['vader_compound'] = vs['compound']
        
        # valence
        valence_scores = get_valence(text, sentiment)
        tweet_features[tweetID]['valence'] = valence_scores['valence']
        tweet_features[tweetID]['arousal'] = valence_scores['arousal']
        tweet_features[tweetID]['dominance'] = valence_scores['dominance']
        
        #topics
        for topic, percent in topics[tweetID].items():
            tweet_features[tweetID][topic] = float("{0:.2f}".format(percent))
        
    return tweet_features



# get features for every tweet in a conversation
# call specialized feature functions as needed

def get_features(conversation, topics, j):
    
    threads = conversation['threads'] #list of thread lists
    tweets = conversation['tweets'] # dict of tweetID : {tweet metadata}
    
    user_features = dict() #dict of form {userID : {features}}
    
    feature_lists = list()
    child_times = dict()
    
    processed = list()
    
    month_dict = {'Jan' : 1, 'Feb' : 2, 'Mar' : 3, 'Apr' : 4, 'May' : 5, 'Jun' : 6,
             'Jul' : 7, 'Aug' : 8, 'Sep' : 9, 'Oct' : 10, 'Nov' : 11, 'Dec' : 12}
    
    #get tweet and user meta data of interest
    for tweetID in tweets:
        
        parentID = tweets[tweetID]['in_reply_to_status_id_str']
            
        #capture timestamp as datetime object
        timestamp = get_timestamp(tweets[tweetID]['created_at'].split(), month_dict)        
        
        #record child times as datetime object
        child_times.setdefault(parentID, dict())
        child_times[parentID][timestamp] = tweetID        
 
        # user features
        userID = tweets[tweetID]['user']['id_str']
        
        #if we haven't already calculated this user's features
        if userID not in user_features:
            user_features.setdefault(userID, dict())
            
            verified_status = tweets[tweetID]['user']['verified']

            # verified = 0 if unverified, 1 if verified
            if verified_status == False:
                user_features[userID]['verified'] = 0
            else:
                user_features[userID]['verified'] = 1            

            user_features[userID]['followers_count'] = tweets[tweetID]['user']['followers_count']
            user_features[userID]['following_count'] = tweets[tweetID]['user']['friends_count']
            user_features[userID]['statuses_count'] = tweets[tweetID]['user']['statuses_count']
            user_features[userID]['favourites_count'] = tweets[tweetID]['user']['favourites_count']

    #turn child times in to dict with ordered children
    parents = dict()
          
    for parentID in child_times:
        parents[parentID] = [c for t, c in sorted(child_times[parentID].items())]
            
    user_feature_order = ['verified', 'followers_count', 'following_count', 'statuses_count', 'favourites_count']
    
    tweet_features = get_tweet_features(tweets, parents, topics, j)
    
    tweet_feature_order = ['favorite_count', 'retweet_count', 'reply count', 'quality',
                           'source', 'xday', 'yday', 'xhour', 'yhour', 'chars', 'url', 'mentions', 'hashtags', 
                           'sentiment', 'vader_neg', 'vader_neu', 'vader_pos', 'vader_compound',
                          'valence', 'arousal', 'dominance', 'topic0', 'topic1', 'topic2', 'topic3',
                          'topic4', 'topic5', 'topic6', 'topic7', 'topic8', 'topic9']
        
    for thread in threads: # for each thread
        threadID = thread[-1] #index thread by leaf
        
        for t in range(2, len(thread)): #for each response 
            features = dict()
            
            tweet_t = thread[t]
            
            if tweet_t not in processed:  #if we haven't seen this tweet before
                processed.append(tweet_t)
                
                i_t = tweets[tweet_t]['user']['id_str']   

                last = thread[t-1]
                i_t_minus = tweets[last]['user']['id_str'] 

                participants = [tweets[tweetID]['user']['id_str'] for tweetID in thread[1:t]]
            
                #build topic array for this tweet
                topic_array = np.zeros(10)
                
                for index in range(10):
                    topic_val = tweet_features[tweet_t]['topic'+str(index)]
                    topic_array[index] = topic_val

                # Construct candidate list
                # exclude root
                # exclude speaker as candidate to respond to themselves
                candidate_list = set(participants)

                if i_t in candidate_list:
                    candidate_list.remove(i_t)

                #### Outcome variable ####
                # For every candidate,
                # If set y = 1 they comment, 0 otherwise

                ## drum roll ##
                respondents = dict() #dict of {userID : tweetID}

                try:
                    children = parents[tweet_t] #tweets in response to current tweet
                    for child in children:
                        respondent = tweets[child]['user']['id_str']
                        respondents[respondent] = child
                    
                except:
                    pass

                for i_t1 in candidate_list:
                    features.setdefault(i_t1, list()) #will have features for every candidate user

                    ### Construct feature vector ###

                    # y:
                    if i_t1 in respondents:
                        features[i_t1].append(1)
                        tweet_t1 = respondents[i_t1] #tweetID of corresponding tweet
                        replies = children.index(child) #number of replies at this point (excluding candidate)
                        
                    else:
                        features[i_t1].append(0)
                        tweet_t1 = 'NA'
                        
                        if tweet_t in parents:
                            replies = len(parents[tweet_t])
                        else:
                            replies = 0

                    # index IDs
                    features[i_t1].append(j)          # j - conversationID
                    features[i_t1].append(threadID)   # threadID
                    features[i_t1].append(tweet_t)    # tweet t
                    features[i_t1].append(tweet_t1)   # tweet t+1
                    features[i_t1].append(i_t)        # i_t user id
                    features[i_t1].append(i_t1)       # i_t1 user id
                    features[i_t1].append(t)          # time t

                    #user t features
                    for feature in user_feature_order:
                        features[i_t1].append(user_features[i_t][feature])

                    comment_i_t_count = participants.count(i_t)
                    features[i_t1].append(comment_i_t_count)

                    #user t + 1 features
                    for feature in user_feature_order:
                        features[i_t1].append(user_features[i_t1][feature])

                    comment_i_t1_count = participants.count(i_t1)
                    features[i_t1].append(comment_i_t1_count)

                    if i_t1 == i_t_minus:          # response
                        features[i_t1].append(1)   # 1 if tweet t was in response to you
                    else:
                        features[i_t1].append(0)   # 0 otherwise

                    # comment t features
                    for feature in tweet_feature_order:
                        features[i_t1].append(tweet_features[tweet_t][feature])
                        
                    #calculate retweets & quality at time t
                    features[i_t1].append(replies)
                    
                    if replies == 0:
                        quality = 0
                    else:
                        retweets = tweet_features[tweet_t]['retweet_count']
                        quality = float(retweets) / float(replies)
                 
                    features[i_t1].append(quality)                    
                    
                    #comment t + 1 features
                    for feature in tweet_feature_order:
                        if i_t1 in respondents:
                            features[i_t1].append(tweet_features[tweet_t1][feature])
                        else:
                            features[i_t1].append('NA')
                            
                    # comment t-1 features
                    #get index of last comment from i_t1
                    prev_turns = [x for x in np.where(np.array(participants) == i_t1)[0] if x < t] #list of i_t1 tweet indices
                    prev_t = max(prev_turns)  #index of last tweet
                    prev_tweet = thread[prev_t] #tweetID of last tweet 
                    t1_prev_t = t - prev_t    #distance from last tweet
                                
                    
                    tminus_topic_array = np.zeros(10)
                    
                    for feature in tweet_feature_order:
                        features[i_t1].append(tweet_features[prev_tweet][feature])
                        
                        #build topic array for t-1 tweet
                        if 'topic' in feature:
                            topic_num = int(feature[-1])
                            tminus_topic_array[topic_num] = tweet_features[prev_tweet][feature]
                        
                    
                    features[i_t1].append(t1_prev_t)
                    
                    #cosign similiarity between t-1 topics and t
                    cos = spatial.distance.cosine(topic_array, tminus_topic_array)
                    features[i_t1].append(cos)
                    
                    #euclidian distance betweet t-1 and t
                    euc = spatial.distance.euclidean(topic_array, tminus_topic_array)
                    features[i_t1].append(euc)
                    
                    # thread features
                    features[i_t1].append(t)                   # thread length
                    features[i_t1].append(len(candidate_list)) # participant count


                for user in features:
                    feature_lists.append(features[user])
                    
            else:
                pass
            
    return feature_lists


### Main Function ###



# Read in data
with gzip.open(path + con_file, 'r') as fp:
    for line in fp.readlines():
        conversations = json.loads(line.decode("utf8"))

print('%s conversations found' %len(conversations))


# identify conversations that don't mention Trump
# so we can trim them from the data
nonTrump = list()

for convoID in conversations:
    tweets = conversations[convoID]['tweets']
    trump_flag = False
    
    for tweetID in tweets:
        text = tweets[tweetID]['full_text']
        if 'Trump' in text or 'trump' in text:
            trump_flag = True
        
    if trump_flag == False:    
        nonTrump.append(convoID)

## read in topic file
with gzip.open(path + topic_file, 'r') as fp:
    for line in fp.readlines():
        all_topics = json.loads(line.decode('utf8'))



#calculate features
errors = 0
obs_count = 0
    
for j in conversations:
    if j not in nonTrump:
        features = get_features(conversations[j], all_topics[j], j)

        if len(features) == 0:
            errors += 1
        else:
            obs_count += len(features)


            # write to file
            with gzip.open(feature_file, 'a') as fp:
                text = ""
                for feature_list in features:
                    line = ','.join(map(str, feature_list)) + '\n'
                    text = text + line

                fp.write(text.encode('utf8'))

print('%s errors out of %s conversations' %(errors, len(conversations)))
print('%s observations' %obs_count)