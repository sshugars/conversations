import json
import gzip
#import nltk
from afinn import Afinn
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

#path
path = '/Users/Shugars/iPython Notebooks/Conversation patterns/'

#build valence dictionary
valience_file = 'BRM-emot-submit.csv'

sentiment = dict()

with open(path + valience_file, 'r') as fp:
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





# calculate features for a collection of tweets

def get_tweet_features(tweets, parents, topics, j):
    afinn = Afinn()
    vader = SentimentIntensityAnalyzer()
    
    tweet_features = dict()
    
    #train LDA on conversation
    
    
    for tweetID in tweets:
        tweet_features.setdefault(tweetID, dict())
        
        #### Tweet features ####
        
        # step 1: easy stuff
        tweet_features[tweetID]['favorite_count'] = tweets[tweetID]['favorite_count']
        retweets = tweets[tweetID]['retweet_count']
        tweet_features[tweetID]['retweet_count'] = retweets      

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
            tweet_features[tweetID]['day'] = 0
        elif post_time[0] == 'Tue':
            tweet_features[tweetID]['day'] = 1
        elif post_time[0] == 'Wed':
            tweet_features[tweetID]['day'] = 2
        elif post_time[0] == 'Thu':
            tweet_features[tweetID]['day'] = 3
        elif post_time[0] == 'Fri':
            tweet_features[tweetID]['day'] = 4
        elif post_time[0] == 'Sat':
            tweet_features[tweetID]['day'] = 5
        elif post_time[0] == 'Sun':
            tweet_features[tweetID]['day'] = 6
        else:
            tweet_features[tweetID]['day'] = -1
            print('No day of the week for tweet %s' %tweetID)

        #get hour in GMT
        tweet_features[tweetID]['hour'] = post_time[3].split(':')[0]    

        #step 3: hard stuff
        text = tweets[tweetID]['text'] 

        #character count
        tweet_features[tweetID]['chars'] = len(text)

        #code url
        #No url = 0, includes url = 1
        if 'http' in text:
            tweet_features[tweetID]['url'] = 1
        else:
            tweet_features[tweetID]['url'] = 0

        #count mentions
        mentions = [c for c in text if c == '@']
        tweet_features[tweetID]['mentions'] = len(mentions)

        #count hashtags
        hashtags = [c for c in text if c == '#']
        tweet_features[tweetID]['hashtags'] = len(hashtags)
        
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
    
    user_features = dict()
    
    parents = dict()
    feature_lists = list()
    
    processed = list()
    
    #get tweet and user meta data of interest
    for tweetID in tweets:
        
        #record lineage
        parentID = tweets[tweetID]['in_reply_to_status_id_str']
        parents.setdefault(parentID, list()) #parent can have more than one child
        parents[parentID].append(tweetID)
        
        # user features
        userID = tweets[tweetID]['user']['id_str']
        
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

            
    user_feature_order = ['verified', 'followers_count', 'following_count', 'statuses_count', 'favourites_count']
    
    tweet_features = get_tweet_features(tweets, parents, topics, j)
    
    tweet_feature_order = ['favorite_count', 'retweet_count', 'reply count', 'quality',
                           'source', 'day', 'hour', 'chars', 'url', 'mentions', 'hashtags', 
                           'sentiment', 'vader_neg', 'vader_neu', 'vader_pos', 'vader_compound',
                          'valence', 'arousal', 'dominance', 'topic0', 'topic1', 'topic2', 'topic3',
                          'topic4', 'topic5', 'topic6', 'topic7', 'topic8', 'topic9']
        
    for thread in threads: # for each thread
        threadID = thread[-1]
        
        for t in range(2, len(thread)): #for each response 
            features = dict()
            
            tweet_t = thread[t]
            
            if tweet_t not in processed:  #if we haven't seen this tweet before
                processed.append(tweet_t)
                
                i_t = tweets[tweet_t]['user']['id_str']   

                last = thread[t-1]
                i_t_minus = tweets[last]['user']['id_str'] 

                participants = [tweets[tweet_t]['user']['id_str'] for tweet_t in thread[1:t]]

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
                        tweet_t1 = respondents[i_t1]
                    else:
                        features[i_t1].append(0)
                        tweet_t1 = 'NA'

                    # index IDs
                    features[i_t1].append(j)          # j
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
                    
                    #comment t + 1 features
                    for feature in tweet_feature_order:
                        if i_t1 in respondents:
                            features[i_t1].append(tweet_features[tweet_t1][feature])
                        else:
                            features[i_t1].append('NA')
                            
                    # comment t-1 features
                    #get index of last comment from i_t1
                    prev_index = len(participants) - 1 - participants[::-1].index(i_t1)
                    prev_tweet = thread[prev_index]
                    t1_prev_t = prev_index + 1 - t
                    
                    for feature in tweet_feature_order:
                        features[i_t1].append(tweet_features[prev_tweet][feature])
                    
                    
                    features[i_t1].append(t1_prev_t)

                    # thread features
                    features[i_t1].append(t)                   # thread length
                    features[i_t1].append(len(candidate_list)) # participant count


                for user in features:
                    feature_lists.append(features[user])
                
                
                    
            else:
                pass
            
    return feature_lists 









## Read in data
con_file = 'conversations.json.gzip'

with gzip.open(path + con_file, 'r') as fp:
    for line in fp.readlines():
        conversations = json.loads(line.decode("utf8"))

print('%s conversations found' %len(conversations))


# identify tweets that don't mention Trump
# so we can trim them from the data

nonTrump = list()

for convoID in conversations:
    tweets = conversations[convoID]['tweets']
    trump_flag = False
    
    for tweetID in tweets:
        text = tweets[tweetID]['text']
        if 'Trump' in text or 'trump' in text:
            trump_flag = True
        
    if trump_flag == False:    
        nonTrump.append(convoID)

## read in topic file
outfile = 'topic_file.json.gzip'

with gzip.open(path + outfile, 'r') as fp:
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
            #concatinate feature list

            # write to file
            feature_file = 'conv_features_test.txt.gzip'

            with gzip.open(feature_file, 'a') as fp:
                text = ""
                for feature_list in features:
                    line = ','.join(map(str, feature_list)) + '\n'
                    text = text + line

                fp.write(text.encode('utf8'))

print('%s errors out of %s conversations' %(errors, len(conversations)))
print('%s observations' %obs_count)