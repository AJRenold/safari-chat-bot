#!/usr/bin/env python

#Description:
#This bot repopulates recommendation topics based on a user's twitter history 
#and fetches real reading recommendations from Safari's API. Please refer to
#write_up.txt for more details. Happy chatting!!
#
#Authors:
#AJ Renold, Siddharth Agrawal

import nltk
import re
import random
import requests
from twitter_api import wordsInTimelineHistory

#This is the API to fetch the Safari recommendation based on the passed url
def fetchSafariRecommendation(url):
    try:
        r = requests.get(url)
        result = r.json()
    except Exception as e:
        print e, 'api fetch error'

    if len(result['recommendations']) > 0:
        fpid, chunk = random.choice(result['recommendations'])['key']
        return { 'fpid': fpid, 'chunk': chunk }
    else:
        return None

class BookChat(object):
    #This function initializes all the variables used in the program.
    def __init__(self, turn_pair_mapping, topics={}):
        self._turn_map = self._compilePairs(turn_pair_mapping)
        self._topics = topics
        self._topic_mentions = []
        self._last_topic = ''
        self._topics_asked = []
        self._recommend_api = 'http://chat-01.heron.safaribooks.com/chat/by-popularity?start=1&topic={topic}' # topic
        self._recommended_url = 'http://www.safariflow.com/library/view/_/{fpid}/{chunk}'

    #This function compiles the conversation pattern from turn pair mapping.
    def _compilePairs(self, turn_pair_mapping):
        for turn, patterns in turn_pair_mapping.items():
            for item in patterns:
                item['pattern'] = re.compile(item['pattern'], re.IGNORECASE)

        return turn_pair_mapping

    #This function searches twitter for topic mentions.
    def _findUserTopicMentions(self, user_name):
        try:
            self._topic_mentions.extend(wordsInTimelineHistory(user_name, self._topics.keys()))
        except Exception as e:
            print e, 'error fetching twitter user history'

    #This function adds the topic mentioned in tweets to topic_mentions list
    def _addUserTopicMentions(self, user_resp):
        self._topic_mentions.extend(
            [word for word in re.sub(r'[^A-Za-z\-\']',' ',user_resp).lower().split(' ')
            if word in self._topics ])

    #This function extracts the topic to be presented to the user either from 
    #the tweet history or at random from the pre-specified list, if no topic matches.
    def _extractTopic(self, match):
        topic = {'topic': ''}
        match_topics = [ word 
                        for word in re.sub(r'[^A-Za-z\-\']', ' ', match.group(0)).lower().split(' ') 
                        if word in self._topics ]

        if len(match_topics) > 0:
            topic['topic'] = random.choice(match_topics)
        elif len(self._topic_mentions) > 0:
            topic['topic'] = random.choice(self._topic_mentions)
        else:
            topic['topic'] = random.choice(self._topics.keys())

        if len(self._topic_mentions) > 0:
            self._topic_mentions.remove(topic['topic'])

        self._topics_asked.append(topic['topic'])
        self._last_topic = topic['topic']
        return topic

    #This function gets the Safari recommendation based on the topic matched.
    def _getRecommendation(self, match):

        if self._last_topic == '':
            topic = self._extractTopic(match)
        else:
            topic = {'topic': self._last_topic}

        topic['topic'] = self._topics[topic['topic']]
        url = self._recommend_api.format(**topic)

        recommendation = fetchSafariRecommendation(url)
        if recommendation:
            return { 'rec': self._recommended_url.format(**recommendation),
                     'topic': topic['topic'] }
        else:
            return None

    def _wildcards(self, response, match):

        resp_kwargs = { 'name': self.user_name }

        if '{topic}' in response:
            resp_kwargs.update(self._extractTopic(match))

        if '{rec}' in response:
            rec = self._getRecommendation(match)
            if rec:
                resp_kwargs.update(rec)
            else:
                return None

        return response.format(**resp_kwargs)

    #This function forms the response for the user based on user input
    def respond(self, user_input, turn):
        self._addUserTopicMentions(user_input)

        while True:
            for item in self._turn_map[turn]:
                match = item['pattern'].match(user_input)

                if match:
                    resp = random.choice(item['responses'])
                    resp = self._wildcards(resp, match)
                    if resp:
                        return resp, item['next_turn'], item['skip_user']

            ## If nothing matches the current turn, go back to turn 1
            turn = 1

    #This function handles the conversation between the user and the chatbot
    def converse(self):
        user_name = ""
        user_input = ""
        skip_user = False
        turn = 1

        print "Hi! I'm the new SuperFlowBot\n"
        print "I'm here to help find you something to read from Safari Books"
        print "I specialize in non-fiction books, so don't expect any Harry Potter from me!\n"
        print "Let me know your Twitter handle so I can find you some personalized recommendations."

        try:
            user_name = raw_input("Your Twitter handle:")
            self.user_name = user_name
        except Exception as e:
            print e, 'at user_name input'

        self._findUserTopicMentions(user_name)

        while True:

            if not skip_user:
                try: user_input = raw_input(user_name + ": ")
                except Exception as e:
                    print e, 'at user_input'

            response, turn, skip_user= self.respond(user_input, turn)
            print 'SuperFlowBot:', response

            if turn == -1:
                break


if __name__ == '__main__':

    #Safari books topic map
    topicMap = {
      "agile": 'agile',
      "agile development": 'agile',
      "analytics": 'analytics',
      "android": 'android',
      "arduino": 'diy-hardware',
      "big data": 'big data',
      "breadboard": 'diy-hardware',
      "business": 'business',
      "circuit-board": 'diy-hardware',
      "cloud": 'cloud',
      "code": 'core programming',
      "consulting": 'business',
      "css": 'css',
      "database": 'databases',
      "design": 'web design',
      "devops": 'devops',
      "diy": 'diy-hardware',
      "do-it-yourself": 'diy-hardware',
      "game development": 'game development',
      "games": 'game development',
      "html": 'html5',
      "html5": 'html5',
      "ios": 'ios',
      "iOS": 'ios',
      "iphone": 'ios',
      "java": 'java',
      "javascript": 'javascript',
      "languages": 'new languages',
      "lean": 'startups',
      "maker": 'diy-hardware',
      "management": 'business',
      "mobile": 'mobile',
      "mongo": 'nosql',
      "nosql": 'nosql',
      "php": 'php',
      "parallel": 'core programming',
      "programming": 'core programming',
      "python": 'python',
      "raspberry pi ": 'diy-hardware',
      "redis": 'nosql',
      "startup": 'startups',
      "teams": 'teams',
      "team work": 'teams',
      "user experience": 'ux & ia',
      "ux": 'ux & ia',
      "visualization": 'data viz',
    }

    #These are the expressions in positive responses from the user
    pos_patterns = r'.*sometimes.*|.*yes.*|.*yup.*|.*yea.*|.*maybe.*|.*sure.*|.*like.*|.*kinda?( of)?.*|.*good.*|.*love.*|.*perfect.*|.*thanks?.*|.*ok.*|.*great.*|.*fine.*|.*cool.*|.*amazing.*|.*awesome.*|.*nice.*'

    #These are the expressions in negative responses from the user
    neg_patterns = r'.*no.*|.*not.*|.*never.*|.*don\'?t.*|.*bad.*|.*n\'t.*|.*useless.*|.*m?eh.*|.*hate.*'

    #This is our turn pair mapping
    map_pairs = {

            # -1 = exits conversation
            # 0 = says goodbye
           0 : [{
                    'pattern': r".*",
                    'responses': ("Thanks @{name}, bye!",
                                "See you later @{name}!"),
                    'next_turn': -1,
                    'skip_user': False
                }
            ],
            ## First turn and convo catch all
           1 : [{
                    'pattern': r".*harry potter.*",
                    'responses': ("@{name}, you're joking right?",
                                "Did you never learn any manners @{name}?"),
                    'next_turn': 1,
                    'skip_user': False
               },
               {
                    'pattern': r".*random.*|.*show me.*|.*books?.*|.*recommend.*",
                    'responses': ("@{name} let's try {rec}",
                                "@{name}, how about this {rec} ?"),
                    'next_turn': -1,
                    'skip_user': False
                },
                {
                    'pattern': r"hi(.*)|hello(.*)|hey(.*)|what's up(.*)|.*greetings.*|.*good.*",
                    'responses' : ("Hi @{name} Do you like {topic} books?",
                                 "Hello @{name} Would you read books about {topic} for fun?",
                                 "Hey @{name} Do you dream about {topic}?",
                                 "How do you do @{name}? Got {topic} on your mind?",
                                 "Hi @{name}! What do you think of {topic}, I love {topic}!"),

                    'next_turn': 2,
                    'skip_user': False
                },
                {
                    'pattern': r".*",
                    'responses': ("@{name} Do you want a book recommendation?",
                                "Are you interested in learning something new @{name}?",
                                "I don't know about that @{name}, but I do know about books, do you know them?",
                                "Change of topic, @{name} do you like to read on Safari Books?",
                                "I have a question @{name}, do you like to read?"),
                    'next_turn': 6,
                    'skip_user': False
                },
            ],
           2 : [
                {
                    'pattern': neg_patterns,
                    'responses': ("Thats too bad @{name}, I thought I was just starting to get to know you",
                                "One more try to help? There's still hope @{name}!"),
                    'next_turn': 4,
                    'skip_user': True
                },
                {
                    'pattern': pos_patterns,
                    'responses': ("I thought so @{name}! you should try reading {rec}",
                                "Interesting... @{name} how about {rec} ?",
                                "@{name} I think you'll like {rec}",
                                "Other people love {rec}, you might too @{name}",
                                "Not to be creepy @{name}, but based on your history you might like {rec}"),
                    'next_turn': 3,
                    'skip_user': True
                }
            ],
           3: [{
                    'pattern': r'.*',
                    'responses': ("Well, what do you think @{name}?",
                                "Let me know what you think @{name}",
                                "How was it @{name}?"),
                    'next_turn': 5,
                    'skip_user': False
                },
            ],
           4: [{
                    'pattern': r'.*',
                    'responses': ("Let's try again @{name}. Do you like {topic}?",
                                "What about {topic}? @{name}!!"),
                    'next_turn': 2,
                    'skip_user': False
               }
            ],
           5: [{
                    'pattern': neg_patterns,
                    'responses': ("Ok @{name}, this is our last chance!",),
                    'next_turn': 4,
                    'skip_user': True
                },
                {
                    'pattern': pos_patterns,
                    'responses': ("Wonderful @{name}! Enjoy!",),
                    'next_turn': -1,
                    'skip_user': True
                }
            ],
           6: [
                {
                    'pattern': neg_patterns,
                    'responses': ("Thats too bad @{name} :( I was just starting to like you!",
                                "Better luck next time @{name}! Bye!"),
                    'next_turn': -1,
                    'skip_user': True
                },
                {
                    'pattern': pos_patterns,
                    'responses': ("Ok @{name}, would you like to read about {topic}?",
                                 "Great! Do you like {topic}? @{name}",
                                 "How do you feel about {topic}? @{name}",
                                 "@{name} Do you like {topic}?",),
                    'next_turn': 2,
                    'skip_user': False
                }
            ]
    }

    bc = BookChat(map_pairs, topics=topicMap)
    bc.converse()
