# conversations
These scripts form a pipeline for scraping and processing conversations from Twitter.

**** get_conversations.py ****
     Retrieve tweet IDs connected to a single tweet ID (e.g., IDs for all tweets in a conversation tree)

     Input: Folder with .json.gzip objects from Twitter API 
     Output: For each seed tweet, a .txt file with connected tweetIDs  


**** get_tweets.py ****
     Retrieve metadata for list of tweet IDs using Twitter's REST API

     Requires: twitter_api_auth_round.json : file with Twitter authorization information

     Input: folder with .txt files of tweet IDs, where each file represents a conversation 
	    (from get_conversations.py)
     Output: For each .txt file, creates a .json.gzip file with full metadata for tweets
	

**** select_conversations.py ****
     Process tweet metadata into single document indexed by conversation ID.

     Input: Folder of .json.gzip files where each file contains 
	    metadata for tweets in the same conversation tree
	    (from get_tweets.py)

     Output: conversation.json.gzip: a single file with all conversation data. Formated as:
   	     convoID : { 
            	tweets : { tweetID: tweet metadata}
            	threads: [[tweetIDs ordered by entry]]        

**** topics.py ****
     Get topics from corpus of tweets

     Input: .json.gzip file of tweet metadata data 
	     (from select_conversations.py)

     Output: 
    	.json.gzip file with topic loadings for each tweetID of format:
        	{convoID : {tweetID : {topic loadings}}}

    	.txt file with top words per topic; comma seperated, 1 topic per line

	gensim save object with LDA model which can be reloaded using:
    	ldamodel = gensim.models.ldamodel.LdaModel.load('ldamodel', mmap='r')


**** features.py ****
     Calculate features for tweets / conversations
 
     Input:
   	.json.gzip file of tweet metadata data. Expected to be of format:
	(from select_conversations.py)

    	.json.gzip file with topic loadings for each tweetID of format:
 	(from topics.py)       

     Output:  .txt.gzip file with matrix of output features


