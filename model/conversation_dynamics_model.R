setwd("/Users/Shugars/Dropbox/research projects/conversation dynamics/replication materials")

# read in data
targ <- read.table("data/conv_features_final.txt.gzip",header=F,sep=",",stringsAsFactors=F)
# varnames

colnames(targ) <- c('y',
                    'j',
                    'threadID',
                    'tweet_t',
                    'tweet_tp1',
                    'i_t',
                    'i_tp1',
                    't',
                    'i_t_verified',
                    'i_t_followers_count',
                    'i_t_following_count',
                    'i_t_statuses_count',
                    'i_t_favourites_count',
                    'i_t_comments_count',
                    'i_tp1_verified',
                    'i_tp1_followers_count',
                    'i_tp1_following_count',
                    'i_tp1_statuses_count',
                    'i_tp1_favourites_count',
                    'i_tp1_comments_count',    
                    'i_tp1_response',
                    'tweet_t_favorite_count', 
                    'tweet_t_retweet_count', 
                    'tweet_t_max_reply_count', 
                    'tweet_t_max_quality',
                    'tweet_t_source', 
                    'tweet_t_xday', 
                    'tweet_t_yday',
                    'tweet_t_xhour', 
                    'tweet_t_yhour', 
                    'tweet_t_chars', 
                    'tweet_t_url', 
                    'tweet_t_mentions', 
                    'tweet_t_hashtags',
                    'tweet_t_sentiment',
                    'tweet_t_vader_neg', 
                    'tweet_t_vader_neu', 
                    'tweet_t_vader_pos', 
                    'tweet_t_vader_compound',
                    'tweet_t_valence',
                    'tweet_t_arousal',
                    'tweet_t_dominance',
                    'tweet_t_topic0', 
                    'tweet_t_topic1', 
                    'tweet_t_topic2', 
                    'tweet_t_topic3',
                    'tweet_t_topic4', 
                    'tweet_t_topic5', 
                    'tweet_t_topic6', 
                    'tweet_t_topic7', 
                    'tweet_t_topic8', 
                    'tweet_t_topic9',
                    'tweet_t_reply_count', 
                    'tweet_t_quality',
                    'tweet_tp1_favorite_count', 
                    'tweet_tp1_retweet_count', 
                    'tweet_tp1_reply_count', 
                    'tweet_tp1_quality',
                    'tweet_tp1_source', 
                    'tweet_tp1_xday', 
                    'tweet_tp1_yday',
                    'tweet_tp1_xhour', 
                    'tweet_tp1_yhour', 
                    'tweet_tp1_chars', 
                    'tweet_tp1_url', 
                    'tweet_tp1_mentions', 
                    'tweet_tp1_hashtags',
                    'tweet_tp1_sentiment',
                    'tweet_tp1_vader_neg', 
                    'tweet_tp1_vader_neu', 
                    'tweet_tp1_vader_pos', 
                    'tweet_tp1_vader_compound',
                    'tweet_tp1_valence',
                    'tweet_tp1_arousal',
                    'tweet_tp1_dominance',
                    'tweet_tp1_topic0', 
                    'tweet_tp1_topic1', 
                    'tweet_tp1_topic2', 
                    'tweet_tp1_topic3',
                    'tweet_tp1_topic4', 
                    'tweet_tp1_topic5', 
                    'tweet_tp1_topic6', 
                    'tweet_tp1_topic7', 
                    'tweet_tp1_topic8', 
                    'tweet_tp1_topic9',
                    'tweet_tm1_favorite_count', 
                    'tweet_tm1_retweet_count', 
                    'tweet_tm1_reply_count', 
                    'tweet_tm1_quality',
                    'tweet_tm1_source', 
                    'tweet_tm1_xday', 
                    'tweet_tm1_yday',
                    'tweet_tm1_xhour', 
                    'tweet_tm1_yhour', 
                    'tweet_tm1_chars', 
                    'tweet_tm1_url', 
                    'tweet_tm1_mentions', 
                    'tweet_tm1_hashtags',
                    'tweet_tm1_sentiment',
                    'tweet_tm1_vader_neg', 
                    'tweet_tm1_vader_neu', 
                    'tweet_tm1_vader_pos', 
                    'tweet_tm1_vader_compound',
                    'tweet_tm1_valence',
                    'tweet_tm1_arousal',
                    'tweet_tm1_dominance',
                    'tweet_tm1_topic0', 
                    'tweet_tm1_topic1', 
                    'tweet_tm1_topic2', 
                    'tweet_tm1_topic3',
                    'tweet_tm1_topic4', 
                    'tweet_tm1_topic5', 
                    'tweet_tm1_topic6', 
                    'tweet_tm1_topic7', 
                    'tweet_tm1_topic8', 
                    'tweet_tm1_topic9',
                    'tweet_tm1_t',
                    'tweet_t_tm1_cos',
                    'tweet_t_tm1_euc',
                    'j_t_thread_length',
                    'j_t_participants'
)

head(targ)
dim(targ)

#scale everything but y values
#add quadratic features for euclean distance and thread length
# ** NB: probably shouldn't scale the topics, and remember to leave one out for the regression**

trimmed <- targ[,c(-(1:8),-(24:25),-(43:52),-(55:85),-(107:116))] # cut out y, indicators, endog vars, t+1 vars, topics
trsc <- scale(trimmed)
targ3 <- cbind('y' = targ$y,
               trsc,                                    # scaled vars
               targ[,c(44:52,108:116)],                 # topics
               'tweet_t_tm1_euc_quad' = trsc[,58]**2,   # quadratic terms
               'j_t_length_quad' = trsc[,59]**2)


targ4c <- targ3[,c(1,8:14,36:50,52,54:57,71:79,61,60,81,2:7,15:16,34:35,17:27,29,31:33,62:70,59,80)]


# OLS baseline
lmout <- lm(y~.,data=targ4c)
summary(lmout)  # r2 of about 0.26

# OLS out-of-sample - 91.1%
set.seed(1)
train <- sample(1:nrow(targ4c),floor(8*nrow(targ4c)/10),replace=F)
dat_tr <- targ4c[train,]
dat_tst <- targ4c[-train,]
1- mean(dat_tst$y) # baseline for this sample: 90.5%

lmoos <- lm(y~.,data=dat_tr)
lyhat <- predict(lmoos, newdata = dat_tst)
lyhat2 <- ifelse(lyhat > 0.5,1,0)
sum(dat_tst$y == lyhat2) / (sum(dat_tst$y == lyhat2) + sum(dat_tst$y != lyhat2))

# Logit full-sample - something wrong, weirdly unstable if remove tweet_t_quality, though OOS works ok without it
logitfullout <- glm(y~.,data=targ4c,family="binomial") # no error clustering
logitfullout_cl <- miceadds::glm.cluster(y~.,data=targ4c,family="binomial",cluster=targ3$tweet_t) # error clustering on prev tweet
summary(logitfullout)

# Logit out-of-sample - 94%
logitoos <- glm(y~.,data=dat_tr,family="binomial")
lyhat <- predict(logitoos, newdata = dat_tst, type="response")
lyhat2 <- ifelse(lyhat > 0.5,1,0)
sum(dat_tst$y == lyhat2) / (sum(dat_tst$y == lyhat2) + sum(dat_tst$y != lyhat2))


# SVM tuned out-of-sample - 97% at 1% in-sample; 98.0% on 10%
library(e1071)
costvalues <- 10^seq(-3,2,1)
svdat <- data.frame(x=as.matrix(targ4c[,-1]),y=as.factor(targ4c$y))
set.seed(1)
train <- sample(1:nrow(svdat),floor(nrow(svdat)/100),replace=F) # NB: should be 80%, but can only manage 10%
svdat_tr <- svdat[train,]
svdat_tst <- svdat[-train,]

tuned.svm <- tune(svm,y~., data=svdat_tr, ranges=list(cost=costvalues), kernel="radial") # takes > 24hrs for 10%
save(tuned.svm,file="svmout.RData")

yhat <- predict(tuned.svm$best.model,newdata=svdat_tst)
save(yhat,file="svmout_oss_preds.RData")
sum(yhat==svdat_tst$y)/length(svdat_tst$y) 
table(predicted=yhat,truth=svdat_tst$y)/length(svdat_tst$y)  
# for 10%:
#          truth
# predicted     0     1
# 0 0.898 0.012
# 1 0.008 0.082


# Latex output from logit
library(stargazer)
vlist <- c("verified", "followers count", "following count", "statuses count", "favourites count", "comments count", "prev response", "favorite count", "retweet count", "reply count", "quality", "source", "xday", "yday", "xhour", "yhour", "chars", "has url", "mentions", "hashtags", "sentiment", "vader neg", "vader pos", "valence", "arousal", "dominance", "time since prev", "topic 2", "topic 3", "topic 4", "topic 5", "topic 6", "topic 7", "topic 8", "topic 9", "topic 10", "participants", "thread length", "thread length^2", "verified", "followers count", "following count", "statuses count", "favourites count", "comments count", "favorite count", "retweet count", "reply count", "quality", "source", "xday", "yday", "xhour", "yhour", "chars", "has url", "mentions", "hashtags", "sentiment", "vader neg", "vader pos", "valence", "arousal", "dominance", "topic 2", "topic 3", "topic 4", "topic 5", "topic 6", "topic 7", "topic 8", "topic 9", "topic 10", "difference", "difference^2")

# multiple testing correction fuction -- BH (FDR) function
bhp <- function(x){
  return(p.adjust(x,"BH"))
}

# Plain version
stargazer(logitfullout, title="title", covariate.labels=vlist, 
          no.space=TRUE, align=TRUE, dep.var.labels.include=F,dep.var.caption = "",
          omit.stat=c("all"),header=FALSE,digits=3,report="vcp*") 

# Verssion with multiple-testing-corrected pvalues
stargazer(logitfullout, title="title", covariate.labels=vlist, 
          no.space=TRUE, align=TRUE, dep.var.labels.include=F,dep.var.caption = "",
          omit.stat=c("all"),header=FALSE,digits=3,report="vcp*",apply.p=bhp) 


# Version with cluster-corrected pvalues
pvcl <- summary(logitfullout_cl)[,4]
stargazer(logitfullout, title="title", covariate.labels=vlist, 
          no.space=TRUE, align=TRUE, dep.var.labels.include=F,dep.var.caption = "",
          omit.stat=c("all"),header=FALSE,digits=3,report="vc*",p=list(pvcl))


# Version with cluster-corrected pvalues plus multiple-testing corrected pvalues
pvcl <- summary(logitfullout_cl)[,4]
stargazer(logitfullout, title="title", covariate.labels=vlist, 
          no.space=TRUE, align=TRUE, dep.var.labels.include=F,dep.var.caption = "",
          omit.stat=c("all"),header=FALSE,digits=3,report="vcp*",p=list(bhp(pvcl)))

# Version with all together, though requires some hand-editing afterwards
rawp <- summary(logitfullout)$coefficients[,4]
pvcl <- summary(logitfullout_cl)[,4]
stargazer(logitfullout,logitfullout,logitfullout,logitfullout, title="title", covariate.labels=vlist, 
          no.space=TRUE, align=TRUE, dep.var.labels.include=F,dep.var.caption = "",
          omit.stat=c("all"),header=FALSE,digits=3,report="c*",p=list(1,rawp,pvcl,bhp(pvcl)),single.row=TRUE)
stargazer(logitfullout, title="title", covariate.labels=vlist, 
          no.space=TRUE, align=TRUE, dep.var.labels.include=F,dep.var.caption = "",
          omit.stat=c("all"),header=FALSE,digits=3,report="vc") 
