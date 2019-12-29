Replication materials for _Why Keep Arguing?  Predicting Participation in Political Conversations Online_. Sarah Shugars and Nick Beauchamp, SAGE Open:  Social Media and Political Participation Global Issue, Forthcoming (2019). Code for this paper are organized as follows:

# get_conversations/
_Scripts for finding tweets and building conversations._


**auth.py**

File with your twitter app credentials
Go to https://developer.twitter.com to apply for a developer account


**get_tweets.py**

Retrieve metadata for list of tweet IDs using Twitter's REST API

     Requires: auth.py : file with Twitter authorization information

     Input: folder with .txt files of tweet IDs, where each file represents a conversation 
	    (from get_conversations.py)
     Output: For each .txt file, creates a .json.gzip file with full metadata for tweets
	

**get_conversations.py**

Retrieve tweet IDs connected to a single tweet ID (e.g., IDs for all tweets in a conversation tree)

	Input: Folder with .json.gzip objects from Twitter API 
	Output: For each seed tweet, a .txt file with connected tweetIDs  


**select_conversations.py**

Process tweet metadata into single document indexed by conversation ID.

     Input: Folder of .json.gzip files where each file contains 
	    metadata for tweets in the same conversation tree
	    (from get_tweets.py)

     Output: conversation.json.gzip: a single file with all conversation data. Formated as:
   	     convoID : { 
            	tweets : { tweetID: tweet metadata}
            	threads: [[tweetIDs ordered by entry]]        


# feature_extraction/

**topics.py**

Get topics from corpus of tweets

     Input: .json.gzip file of tweet metadata data 
	     (from select_conversations.py)

     Output: 
    	.json.gzip file with topic loadings for each tweetID of format:
        	{convoID : {tweetID : {topic loadings}}}

    	.txt file with top words per topic; comma seperated, 1 topic per line

	    gensim save object with LDA model which can be reloaded using:
    	ldamodel = gensim.models.ldamodel.LdaModel.load('ldamodel', mmap='r')


**features.py**

Calculate features for tweets / conversations
 
     Input:
   	.json.gzip file of tweet metadata data. Expected to be of format:
	(from select_conversations.py)

    .json.gzip file with topic loadings for each tweetID of format:
 	(from topics.py)       

     Output:  
         .txt.gzip file with matrix of output features


# model/

**conversation_dynamics_model.R**

Run logit and SVM on calculated features

	Input: .txt.gzip file of feature matrix (one row = one observation)
	
	Output: Stargazer / latex summary of results
	
# Data 

To respect the privacy of individuals whose tweets our in our dataset, we've included a list of ids for all tweets used (`tweet_ids.txt`) rather than include the raw data itself. In order to replicate this study, researchers should begin by scraping these tweets. This process will ensure that we do not violate users privacy by sharing any tweet data which a user has elected to delete following our data collection window.