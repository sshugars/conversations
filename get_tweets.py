import twitter
import json
import gzip
import glob
from time import sleep

# validate credentials
auth_fn = "../twitter_api_auth_round3.json"

my_account = json.load(open(auth_fn, 'r'))

auth = twitter.oauth.OAuth(my_account["access_token"],
                           my_account["access_token_secret"],
                           my_account["api_key"],
                           my_account["api_secret"])

my_twitter_app = twitter.Twitter(auth = auth)

# processed conversations
processed = list()

path = '../conversations/'

for filename in glob.glob(path + '*.json.gzip'):
	convoID = filename.split('.')[-3].split('_')[-1]
	processed.append(convoID)

print('%s conversations already processed' %len(processed))

# define path
path = '../convo_ids/'
limit = 0

for filename in glob.glob(path + '*.txt'):
	seed_id = filename.split('_')[-1].split('.')[0]
	tweet_ids = list()

	if seed_id not in processed:
		print('Searching file: %s' %filename)
		
		with open(filename) as fp:
			for line in fp.readlines():
				tweet_ids.append(line.strip())

		print('%s tweets found' %len(tweet_ids))

		# use REST API for JSON of tweets
		full_tweets = dict()
		not_found = list()

		for tweet_id in tweet_ids:   
			limit += 1
			
			#check if we need to sleep
			if limit > 899:
				print("Sleeping...")
				sleep(60 * 15) #sleep 15 minutes
				limit = 0
			
			else:
				try:
					search_results = my_twitter_app.statuses.show(id = tweet_id, tweet_mode='extended')
					full_tweets[tweet_id] = search_results
				except:
					not_found.append(tweet_id)

		conv_out = '../conversations/conv_' + str(seed_id) + '.json.gzip'
		error_log = '../errors/not_found_' + str(seed_id) + '.txt' 

		if len(full_tweets) > 0:
			with gzip.open(conv_out, 'w') as fout:
				print >> fout, json.dumps(full_tweets)
		
		with open(error_log, 'w') as f:
			f.write('\n'.join(not_found))
		
		print('%s tweets written to file. %s not found.\n' %(len(full_tweets), len(not_found)))
