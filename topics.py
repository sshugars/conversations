
from nltk.corpus import stopwords 
from nltk.stem.wordnet import WordNetLemmatizer
import string
import gensim
from gensim import corpora

# Set up
stop = set(stopwords.words('english'))
exclude = set(string.punctuation) 
lemma = WordNetLemmatizer()

def clean(doc):
    stop_free = " ".join([i for i in doc.lower().split() if i not in stop])
    punc_free = ''.join(ch for ch in stop_free if ch not in exclude)
    normalized = " ".join(lemma.lemmatize(word) for word in punc_free.split())
    return normalized


#transform tweet metadata into format we need
def get_topics(tweets):

    tweet_text = dict()
    
    for tweetID in tweets:
        text = tweets[tweetID]['text'] 
        tweet_text[tweetID] = text
    
    topics = topic_model(tweet_text)
    
    return topics

#run topic model for single conversation tree
 def topic_model(tweet_text):
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
    
    return topics


### Run topic model on corpus of tweet conversations

## Read in data
con_file = 'conversations.json.gzip'

with gzip.open(con_file, 'r') as fp:
    for line in fp.readlines():
        conversations = json.loads(line.decode("utf8"))

print('%s conversations found' %len(conversations))


#find topics
all_topics = dict()

for j in conversations:
    all_topics.setdefault(j, dict())
    tweets = conversations[j]['tweets']
    
    topics = get_topics(tweets)
    
    for tweet in topics:
        all_topics[j][tweet] = topics[tweet]


#write topics to file
outfile = 'topic_file.json.gzip'
with gzip.open(outfile, 'w') as fp:
    fp.write(json.dumps(all_topics).encode('utf8'))
        