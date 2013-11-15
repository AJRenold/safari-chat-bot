import re

from settings import (
        consumer_key,
        consumer_secret,
        access_token,
        access_token_secret
        )

from twitter import *

def wordsInTimelineHistory(user, words):

    t = Twitter(
        auth=OAuth(access_token, access_token_secret,
                    consumer_key, consumer_secret
            ))

    tweets = t.statuses.user_timeline(id=user, count=200)

    tweet_content_set =  set([ word
            for tweet in tweets
            for word in re.sub(r'[^A-Za-z\-\']',' ', tweet['text']).lower().split(' ') 
            ])

    return [ word for word in words if word in tweet_content_set ]

if __name__ == '__main__':

    ## Quick sanity test
    words = ['python', 'agile', 'nosql']
    print wordsInTimelineHistory('ajrenold', words)
    print
    print wordsInTimelineHistory('wirelesstech', words)
    print
    print wordsInTimelineHistory('liza', words)
