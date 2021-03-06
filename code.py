# Installing and Importing Libraries

import nltk

nltk.download('punkt')
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from math import log
import pandas as pd
import numpy as np
import re

# The Dataset

tweets = pd.read_csv('dataset.csv')
tweets.drop(['Unnamed: 0'], axis=1, inplace=True)
tweets['label'].value_counts()

# Wordcloud Analysis

positive_words = ' '.join(list(tweets[tweets['label'] == 0]['message']))
positive_wc = WordCloud(background_color='white', width=1024, height=512, collocations=False).generate(positive_words)
plt.figure(figsize=(10, 5), facecolor='k')
plt.imshow(positive_wc)
plt.axis('off'),
plt.tight_layout(pad=0)
plt.show()

depressive_words = ' '.join(list(tweets[tweets['label'] == 1]['message']))
depressive_wc = WordCloud(width=1024, height=512, collocations=False).generate(depressive_words)
plt.figure(figsize=(10, 5), facecolor='k')
plt.imshow(depressive_wc)
plt.axis('off')
plt.tight_layout(pad=0)
plt.show()

# Training and Testing Data

totalTweets = 8000 + 2314
trainIndex, testIndex = list(), list()
for i in range(tweets.shape[0]):
    if np.random.uniform(0, 1) < 0.7:
        trainIndex += [i]
    else:
        testIndex += [i]
trainData = tweets.iloc[trainIndex]
testData = tweets.iloc[testIndex]

trainData['label'].value_counts()

testData['label'].value_counts()

# Data Pre-processing

def process_message(message, lower_case=True, stem=True, stop_words=True, gram=2):
    if lower_case:
        message = message.lower()
    words = word_tokenize(message)
    words = [w for w in words if len(w) > 2]
    if gram > 1:
        w = []
        for i in range(len(words) - gram + 1):
            w += [' '.join(words[i:i + gram])]
        return w
    if stop_words:
        sw = stopwords.words('english')
        words = [word for word in words if word not in sw]
    if stem:
        stemmer = PorterStemmer()
        words = [stemmer.stem(word) for word in words]
    return words

# Creating the TweetClassifier

class TweetClassifier(object):
    
    def __init__(self, trainData, method='tf-idf'):
        self.tweets, self.labels = trainData['message'], trainData['label']
        self.method = method

# Defining our Functions

    def get_TF_IDF(self):
        self.prob_depressive = dict()
        self.prob_positive = dict()
        self.sum_tf_idf_depressive = 0
        self.sum_tf_idf_positive = 0
        for word in self.tf_depressive:
            self.prob_depressive[word] = (self.tf_depressive[word]) * log(
                (self.depressive_tweets + self.positive_tweets) \
                / (self.idf_depressive[word] + self.idf_positive.get(word, 0)))
            self.sum_tf_idf_depressive += self.prob_depressive[word]
        for word in self.tf_depressive:
            self.prob_depressive[word] = (self.prob_depressive[word] + 1) / (
                        self.sum_tf_idf_depressive + len(list(self.prob_depressive.keys())))
        for word in self.tf_positive:
            self.prob_positive[word] = (self.tf_positive[word]) * log((self.depressive_tweets + self.positive_tweets) / (self.idf_depressive.get(word, 0) + self.idf_positive[word]))
            self.sum_tf_idf_positive += self.prob_positive[word]
        for word in self.tf_positive:
            self.prob_positive[word] = (self.prob_positive[word] + 1) / (self.sum_tf_idf_positive + len(list(self.prob_positive.keys())))
        self.prob_depressive_tweet, self.prob_positive_tweet = self.depressive_tweets / self.total_tweets, self.positive_tweets / self.total_tweets

    def calc_TF_IDF(self):
        noOfMessages = self.tweets.shape[0]
        self.depressive_tweets, self.positive_tweets = self.labels.value_counts()[1], self.labels.value_counts()[0]
        self.total_tweets = self.depressive_tweets + self.positive_tweets
        self.depressive_words = 0
        self.positive_words = 0
        self.tf_depressive = dict()
        self.tf_positive = dict()
        self.idf_depressive = dict()
        self.idf_positive = dict()
        for i in range(noOfMessages):
            message_processed = process_message(self.tweets.iloc[i])
            count = list()
            for word in message_processed:
                if self.labels.iloc[i]:
                    self.tf_depressive[word] = self.tf_depressive.get(word, 0) + 1
                    self.depressive_words += 1
                else:
                    self.tf_positive[word] = self.tf_positive.get(word, 0) + 1
                    self.positive_words += 1
                if word not in count:
                    count += [word]
            for word in count:
                if self.labels.iloc[i]:
                    self.idf_depressive[word] = self.idf_depressive.get(word, 0) + 1
                else:
                    self.idf_positive[word] = self.idf_positive.get(word, 0) + 1
                                       
    def train(self):
        self.calc_TF_IDF()
        if self.method == 'tf-idf':
            self.get_TF_IDF()

    def classify(self, processed_message):
        pDepressive, pPositive = 0, 0
        for word in processed_message:
            if word in self.prob_depressive:
                pDepressive += log(self.prob_depressive[word])
            else:
                if self.method == 'tf-idf':
                    pDepressive -= log(self.sum_tf_idf_depressive + len(list(self.prob_depressive.keys())))
            if word in self.prob_positive:
                pPositive += log(self.prob_positive[word])
            else:
                if self.method == 'tf-idf':
                    pPositive -= log(self.sum_tf_idf_positive + len(list(self.prob_positive.keys())))
            pDepressive += log(self.prob_depressive_tweet)
            pPositive += log(self.prob_positive_tweet)
        return pDepressive >= pPositive

    def predict(self, testData):
        result = dict()
        for (i, message) in enumerate(testData):
            processed_message = process_message(message)
            result[i] = int(self.classify(processed_message))
        return result

# Results

def metrics(labels, predictions):
    true_pos, true_neg, false_pos, false_neg = 0, 0, 0, 0
    for i in range(len(labels)):
        true_pos += int(labels.iloc[i] == 1 and predictions[i] == 1)
        true_neg += int(labels.iloc[i] == 0 and predictions[i] == 0)
        false_pos += int(labels.iloc[i] == 0 and predictions[i] == 1)
        false_neg += int(labels.iloc[i] == 1 and predictions[i] == 0)
    precision = true_pos / (true_pos + false_pos)
    recall = true_pos / (true_pos + false_neg)
    Fscore = 2 * precision * recall / (precision + recall)
    accuracy = (true_pos + true_neg) / (true_pos + true_neg + false_pos + false_neg)

    print("Precision: ", precision)
    print("Recall: ", recall)
    print("F-score: ", Fscore)
    print("Accuracy: ", accuracy)
    

sc_tf_idf = TweetClassifier(trainData, 'tf-idf')
sc_tf_idf.train()
preds_tf_idf = sc_tf_idf.predict(testData['message'])
metrics(testData['label'], preds_tf_idf)

# Predictions

pm = process_message('Feeling happy, motivated and ready to positively impact the world!')
sc_tf_idf.classify(pm)

pm = process_message('1382  Willis Avenue. THE best ice cream. Thank me later.')
sc_tf_idf.classify(pm)

pm = process_message('My baby boy just said his first words - feeling over the moon!')
sc_tf_idf.classify(pm)

pm = process_message('I used to be overweight, demotivated, and depressed. Boy have times changed')
sc_tf_idf.classify(pm)

pm = process_message('Feeling hopeless, depressed and miserable all the time.')
sc_tf_idf.classify(pm)

pm = process_message('Why do I always feel like I could cry at any moment?')
sc_tf_idf.classify(pm)

pm = process_message('I am never going to lose 20lbs - why even bother trying?')
sc_tf_idf.classify(pm)

pm = process_message('All I want is to feel happy and fulfilled again...')
sc_tf_idf.classify(pm)
