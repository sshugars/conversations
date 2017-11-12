"""
Retrieve metadata for list of tweet IDs using Twitter's REST API

This script will iterate through a folder of .txt files, where each file
contains break-seperated tweetIDs of tweets to get metadata for. Intended to 
be used as the processing step after get_conversations.py, which will produce
separate .txt files of tweetIDs connected to a given seed tweet.

Requires: 
	twitter_api_auth_round.json : file with Twitter authorization information

Output:
	For each .txt file, creates a .json.gzip file with full metadata for tweets
	
"""

### Parameters to set ###
in_path = '../convo_ids/'  		# path for input .txt files with tweetIDs
out_path =  '../conversations/'        	# path for output .json.gzip files with tweet metadata
error_path = '..errors/'         	# path to record error log
### End customization


import twitter
import json
import gzip
import glob
from time import sleep

### Step 1: validate credentials ###
auth_fn = "twitter_api_auth_round.json"

my_account = json.load(open(auth_fn, 'r'))

auth = twitter.oauth.OAuth(my_account["access_token"],
                           my_account["access_token_secret"],
                           my_account["api_key"],
                           my_account["api_secret"])

my_twitter_app = twitter.Twitter(auth = auth)

### Step 2: Check what's already been processed, in case of restart
processed = list()

for filename in glob.glob(out_path + '*.json.gzip'):
	convoID = filename.split('.')[-3].split('_')[-1]
	processed.append(convoID)

print('%s conversations already processed' %len(processed))

### Step 3: iterate through files and get metadata for tweets ###
limit = 0 #track rate limit - built in API call for this doesn't seem to work properly

for filename in glob.glob(path + '*.txt'):
	seed_id = filename.split('_')[-1].split('.')[0] #infer seed_id from filename
	
	if seed_id not in processed: # If we haven't processed this file already...
		print('Searching file: %s' %filename)
		
		# Get list of tweetIDs to search from this file
		tweet_ids = list() 
		with open(filename) as fp:
			for line in fp.readlines():
				tweet_ids.append(line.strip())
		print('%s tweets found' %len(tweet_ids))

		### Step 4: use REST API to get JSON metadate for each tweet ###
		full_tweets = dict()	# store metadata for every tweet in this file
		not_found = list()	# list of tweetIDs unable to retrieve

		for tweet_id in tweet_ids:   
			
			#Update limit count and check if we need to sleep
			limit += 1
			if limit > 899:
				print("Sleeping...")
				sleep(60 * 15) #sleep 15 minutes
				limit = 0
			else:
				try:
					# use REST API to search for tweet
					# tweet_mode='extended' gives full, rather than truncated text
					search_results = my_twitter_app.statuses.show(id = tweet_id, tweet_mode='extended')
					full_tweets[tweet_id] = search_results
				except:
					not_found.append(tweet_id)

		conv_out = out_path + 'conv_' + str(seed_id) + '.json.gzip'
		error_log = error_path + 'not_found_' + str(seed_id) + '.txt' 

		# if we found tweets...
		if len(full_tweets) > 0:
			with gzip.open(conv_out, 'w') as fout:
				print >> fout, json.dumps(full_tweets)
		
		# if we found errors...
		with open(error_log, 'w') as f:
			f.write('\n'.join(not_found))
		
		print('%s tweets written to file. %s not found.\n' %(len(full_tweets), len(not_found)))
