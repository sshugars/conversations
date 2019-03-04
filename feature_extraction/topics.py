"""
Get topics from corpus of tweets

Included functions:
    clean : helper function to pre-process data
    topic model: function to run topic model on corpus of documents

Input:
   .json.gzip file of tweet metadata data. Expected to be of format:
       convoID : { 
            tweets : { tweetID: tweet metadata}
            threads: [[tweetIDs ordered by entry]]        
                }

Output: 
    .json.gzip file with topic loadings for each tweetID of format:
        {convoID : 
             {tweetID : {topic loadings}}}

    .txt file with top words per topic; comma seperated, 1 topic per line

    gensim save object with LDA model which can be reloaded using:
    ldamodel = gensim.models.ldamodel.LdaModel.load('ldamodel', mmap='r')

"""

### Parameters to set ###
con_file = '../conversations.json.gzip'     #file with tweet data from conversations
tweet_outfile = '../topic_file2.json.gzip'   #output of topic loadings on tweet
topic_outfile = '../top_words.txt'          #save top words per topic
lda_output = 'ldamodel2'                  #save model
seed =  653                              #helpful to reproduce results; seed selected randomly
num_words = 10                           #record the top num_words for each topic
mallet_file = 'MALLET.txt'               #import stopwords from MALLET
### End customization ###  

from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
import string
import gensim
from gensim import corpora
from gensim.parsing.preprocessing import STOPWORDS
import gzip
import json
import numpy as np

# Set up
#read in MALLET stopwords
MALLET_stop = list()
with open(mallet_file, 'r') as fp:
    for word in fp.readlines():
        MALLET_stop.append(word.strip())


stop = set(stopwords.words('english')).union(set(stopwords.words('spanish'))).union(set(STOPWORDS)).union(set(MALLET_stop))
stop.add('trump')
exclude = set(string.punctuation)
exclude.add('’')


def clean(doc):
    punc_free = ''.join(token if token not in exclude else " " for token in doc) #replace punctuation with spaces: you're -> you re
    stop_free = " ".join([i for i in punc_free.lower().split() if i not in stop])
    return stop_free


def topic_model(tweet_text):
    """
    Run topic model on a corpus of tweets

    Arguments:
        tweet_text : dict of format {tweetID : tweet text}

    Returms:
        topics : topic loadings on to tweets. dict of the form:
                {tweetID : {topic0 : float}. {topic1 : float}...}
    """

    topics = dict()
    
    tweetIDs = [tweetID for tweetID, text in tweet_text.items()]
    documents = [text for tweetID, text in tweet_text.items()]
    
    doc_clean = [clean(doc).split() for doc in documents]  

    # Creating the term dictionary of our courpus, where every unique term is assigned an index. 
    dictionary = corpora.Dictionary(doc_clean)

    # Converting list of documents (corpus) into Document Term Matrix using dictionary prepared above.
    doc_term_matrix = [dictionary.doc2bow(doc) for doc in doc_clean]

    # Creating the object for LDA model using gensim library
    Lda = gensim.models.ldamodel.LdaModel

    # Running and Training LDA model on the document term matrix.
    ldamodel = Lda(doc_term_matrix, num_topics=10, id2word = dictionary, passes=50)
    
    ldamodel.save(lda_output) #save LDA output

    lda_corpus = ldamodel[doc_term_matrix]
    
    for i, doc in enumerate(lda_corpus):   
        tweetID = tweetIDs[i]
        
        topics.setdefault(tweetID, dict())
        
        for topic, percent in doc:
            topics[tweetID]['topic'+str(topic)] = percent

        #if topic missing
        for i in range(10):
            if 'topic'+str(i) not in topics[tweetID]:
                topics[tweetID]['topic'+str(i)] = 0.0
    
    return topics, ldamodel


### Main Function ###

# Read in tweet data
with gzip.open(con_file, 'r') as fp:
    for line in fp.readlines():
        conversations = json.loads(line.decode("utf8"))

print('%s conversations found' %len(conversations))


#set the seed for reproducibility
np.random.seed(seed)

tweet_text = dict()         #dict of format {tweetID : tweet text}
convo_tweet_ids = dict()    #dict of format {convoID : [tweetIDs]}


#build corpus
for j in conversations:
    convo_tweet_ids.setdefault(j, list())

    tweets = conversations[j]['tweets']

    for tweetID in tweets:
        raw_text = tweets[tweetID]['full_text']
    
        #remove handles from text
        #metadata `entites' unreliable for this task
        text = " ".join([word for word in raw_text.split() if word[0] != '@'])

        tweet_text[tweetID] = text

        convo_tweet_ids[j].append(tweetID)

#run topic model on all tweet text
topics, ldamodel = topic_model(tweet_text)

#record topic values in dict indexed by convoID

all_topics = dict() 
for j in convo_tweet_ids:
    all_topics.setdefault(j, dict())

    for tweetID in convo_tweet_ids[j]:
        all_topics[j][tweetID] = topics[tweetID]


#write topics to file
with gzip.open(tweet_outfile, 'w') as fp:
    fp.write(json.dumps(all_topics).encode('utf8'))

#write top words per topic to file
output = dict()

for num, vals in ldamodel.show_topics(num_topics=10, num_words=num_words, formatted=False):
    words, val = zip(*vals)
    output[num] = ','.join(words)

with open(topic_outfile, 'w') as fp:
    for words in output.values():
        fp.write(words + '\n')



        