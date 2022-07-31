import credentials
import tweepy
import mysql.connector
from tweepy.streaming import StreamListener
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import json
import pdb
import re
import argparse
 
 
# Initialize parser
parser = argparse.ArgumentParser()

parser.add_argument("-k", "--keywords", type=str, required=True,
                        help="Keywords to filter stream (comma seperated, wrap in quotation marks")

parser.add_argument("-c", "--count", type=str, required=True,
                        help="Number of tweets to filter stream (comma seperated, wrap in quotation marks")

args = parser.parse_args()


search_words = args.keywords

#search_words = search_words.split(',')

class TwitterAnalyzer():

	def store_hashtags(self, text):
		matches = re.findall('#(\w+)', text)

		if len(matches) > 0:
			hashtags = [match for match in matches]
			return hashtags
		else:
			return None

	def clean_text(self, text):
		#Remove URLs
		clean_text = re.sub(r'http\S+', '', text)

		#Remove Username Handles
		clean_text = re.sub('@[^\s]+', '', clean_text)

		#Remove Hashtags
		clean_text = re.sub('#[^\s]+', '', clean_text)

		#Replace newline with space
		clean_text = clean_text.replace('\n', ' ')

		return clean_text.strip()

	def get_sentiment_score(self, text):
		analyzer = SentimentIntensityAnalyzer()
		return analyzer.polarity_scores(text)

class DatabaseManager():

	def __init__(self, host, password, user = "root", database = None):
		self.mydb = mysql.connector.connect(
				host = host,
				user = user,
				password = password,
				database = database
			)
		self.mycursor = self.mydb.cursor()

		# print(self.mydb)

	def create_database(self, database_name = "twitter_database"): 
		self.mycursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(database_name))

	def create_table(self, table_name = "tweets"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
			id VARCHAR(255) PRIMARY KEY,\
			retweet_count INT,\
			created_at DATETIME,\
			favorite_count INT,\
			author VARCHAR(255),\
			neg_score FLOAT,\
			neu_score FLOAT,\
			pos_score FLOAT,\
			compound_score FLOAT,\
			hashtags VARCHAR(255),\
			text LONGTEXT,\
			follower_count INT,\
			search_words VARCHAR(255))".format(table_name))
				
		#self.mycursor.execute("TRUNCATE tweets")

	def create_table_hashtag(self, table_name = "hashtag"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
            hashtag_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\
            hashtag_text VARCHAR(255)  NOT NULL ,\
            hashtag_event INT NOT NULL,\
            FOREIGN KEY(hashtag_event) REFERENCES event(event_id) ON UPDATE CASCADE)".format(table_name))
		#self.mycursor.execute("TRUNCATE hashtag")
    
	def create_table_event(self, table_name = "event"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
            event_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\
            event_name VARCHAR(255) NOT NULL)".format(table_name))
		#self.mycursor.execute("TRUNCATE event")


	def create_table_user(self, table_name = "users"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
            user_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\
            user_name VARCHAR(255) NOT NULL,\
            user_followers INT)".format(table_name))
		#self.mycursor.execute("TRUNCATE user")
		

	def create_table_has_ht(self, table_name = "has_ht"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
            has_ht_tid VARCHAR(255) NOT NULL ,\
            has_ht_hid INT NOT NULL ,\
			PRIMARY KEY(has_ht_tid,has_ht_hid),\
            FOREIGN KEY(has_ht_tid) REFERENCES tweets(id) ON UPDATE CASCADE,\
			FOREIGN KEY(has_ht_hid) REFERENCES hashtag(hashtag_id) ON UPDATE CASCADE)".format(table_name))
		#self.mycursor.execute("TRUNCATE has_ht")

	def create_table_tweets_about(self, table_name = "tweets_about"):
		self.mycursor.execute("CREATE TABLE IF NOT EXISTS {} (\
            tweets_about_uid INT NOT NULL,\
            tweets_about_eid INT NOT NULL ,\
			PRIMARY KEY(tweets_about_uid,tweets_about_eid),\
            FOREIGN KEY(tweets_about_uid) REFERENCES users(user_id)  ON UPDATE CASCADE ,\
            FOREIGN KEY(tweets_about_eid) REFERENCES event(event_id) ON UPDATE CASCADE )".format(table_name))
		#self.mycursor.execute("TRUNCATE tweets_about")


	#Emojis require that you use utf8mb4 encoding instead of the traditional utf8
	def alter_table_for_emojis(self, database_name = "twitter_database", table_name = "tweets"):
		self.mycursor.execute('SET NAMES utf8mb4')
		self.mycursor.execute("SET CHARACTER SET utf8mb4")
		self.mycursor.execute("SET character_set_connection=utf8mb4")


	def insert_data(self, id, created_at, author, text, retweet_count, favorite_count,
		neg_score, neu_score, pos_score, compound_score, hashtags, follower_count, search_words):
		#Tweets
		sql = """
			INSERT INTO {} (id, created_at, author, text, retweet_count, favorite_count, neg_score, neu_score, pos_score, compound_score, hashtags, follower_count, search_words)
				VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		""".format("tweets")

		val = (id, created_at, author, text, retweet_count, favorite_count, neg_score,
			neu_score, pos_score, compound_score, hashtags, follower_count, search_words)
		
		self.mycursor.execute(sql, val)
		self.mydb.commit()

	
		###################################################################################
		# Event
		v=1
		try:
			sql = """
				INSERT INTO {} (event_id,event_name) VALUES(%s,%s)
				""".format("event")
		
			val = (str(v),search_words)
			#print("Inserting event")
			self.mycursor.execute(sql, val)
			self.mydb.commit()
		except :
			pass
		
		# #########################################################################################3
		# #User
		sql = """
			INSERT INTO {} (user_name,user_followers)
				VALUES (%s, %s)
		""".format("users")

		val = (author,follower_count)

		self.mycursor.execute(sql, val)
		self.mydb.commit()
	
		####################################################################
		#Hashtag
		##print("Type of hashtags", type(hashtags))
		if hashtags:
			for hashtag in hashtags.split(','):
				try:
					sql = """
						INSERT INTO {} (hashtag_text,hashtag_event)
							VALUES (%s, %s)
					""".format("hashtag")

					val = (hashtag, str(1))

					self.mycursor.execute(sql, val)
					self.mydb.commit()
					#print("hello")

					sql="SELECT MAX(hashtag_id) FROM hashtag"
					self.mycursor.execute(sql)
					res=self.mycursor.fetchall()
					#print("MAX VALUE",res)
					if res:
						hashid=res[0][0]
						sql = """
						INSERT INTO {} (has_ht_tid,has_ht_hid)
							VALUES (%s,%s)
						""".format("has_ht")

						val = (id, hashid)

						self.mycursor.execute(sql, val)
						self.mydb.commit()


				except:
					pass
		
		# ################################################################
		#Find hashtag ID
		#a=-1
		# res=[]
		# try:
		# 	print(hashtags)
		# 	sql="SELECT hashtag_id FROM hashtag WHERE hashtag_text='{}'".format(hashtags)
		# 	#print(hashtags)
		# 	self.mycursor.execute(sql)
		# 	res=self.mycursor.fetchall()
			
		# 	# for x in res:
		# 	# 	a=x
			
		# except:
		# 	pass

		# # 	#################################################################
		# #has_ht

		# print(res)
		# if res:
		# 	for x in res:
		# 		try:

		# 			sql = """
		# 				INSERT INTO {} (has_ht_tid,has_ht_hid)
		# 					VALUES (%s,%s)
		# 			""".format("has_ht")

		# 			val = (id, x[0])

		# 			self.mycursor.execute(sql, val)
		# 			self.mydb.commit()
		# 		except:
		# 			pass
	
		###################################################################################3
		#finding user ID
		b=-1
		try:
			sql="SELECT user_id FROM users WHERE user_name='{}' ".format(author)
			self.mycursor.execute(sql)
			res=self.mycursor.fetchall()
			
			for x in res:
				b=x[0]
		except:
			pass
		##################################################################################
		#tweets_about
		#print("USER ID IS",b)
		if b!=-1:
			sql = """
				INSERT INTO {} (tweets_about_uid,tweets_about_eid) VALUES (%s,%s)
			""".format("tweets_about")
			#print(sql)
			v = (b,1)

			self.mycursor.execute(sql,v)
			self.mydb.commit()

	####################  END OF INSERTIONS ########################################3333333

	# Method for deleting the database in case of errors, used for debugging
	def delete_database(self):
		sql = "DROP DATABASE twitter_database"
		self.mycursor.execute(sql)

	#Method that contains all of my debugging code, should delete later
	def debug(self):

		print("DATABASES ARE BELOW: ")
		self.mycursor.execute("SHOW DATABASES")
		for db in self.mycursor:
			print(db)

		self.mycursor.execute("SELECT * FROM tweets")
		myresult = self.mycursor.fetchall()

		print("DATA: ")
		for row in myresult:
			print(row)

class TwitterListener(StreamListener):

	def __init__(self, num_tweets_to_grab):
		super(TwitterListener, self).__init__()
		self.counter = 0
		self.num_tweets_to_grab = num_tweets_to_grab
		self.twitter_analyzer = TwitterAnalyzer()
		self.database_manager = DatabaseManager("localhost", "root")

		#Create database and table on initialization of TwitterListener
		self.database_manager.create_database()

		#Reinitialize database manager to connect with the database we just created
		self.database_manager = DatabaseManager("localhost", "root", database="twitter_database")
		self.database_manager.mycursor.execute("drop table if exists has_ht")
		self.database_manager.mycursor.execute("drop table if exists tweets_about")
		self.database_manager.mycursor.execute("drop table if exists users")
		self.database_manager.mycursor.execute("drop table if exists tweets")
		self.database_manager.mycursor.execute("drop table if exists hashtag")
		self.database_manager.mycursor.execute("drop table if exists event")

		self.database_manager.create_table()
		self.database_manager.create_table_event()
		
		self.database_manager.create_table_hashtag()
		
		self.database_manager.create_table_user()
		self.database_manager.create_table_has_ht()
		self.database_manager.create_table_tweets_about()

		self.database_manager.alter_table_for_emojis()

	def on_status(self, status):

		if self.counter == self.num_tweets_to_grab:
			return False

		#Avoid retweeted info
		if 'retweeted_status' in dir(status):
			return True

		# # # Getting Useful Attributes form Each Tweet # # #

		#Twitter recently increased max character count for tweets... 
		#therefore the new tweets with more characters have the full text in 'extended_tweet'
		#old tweets full text can be found in 'text'
		if 'extended_tweet' in dir(status):
			text = status.extended_tweet['full_text']

		else:
			text = status.text

		id = status.id_str #Str: This id will be used as primary key in SQL database
		created_at = status.created_at #Datetime: Specifying when tweet was created
		retweet_count = status.retweet_count #Int: number of times tweet was retweeted
		favorite_count = status.favorite_count #Int: number of times tweet was favorited
		author = status.user.screen_name #Str: username of the tweet's author
		follower_count = status.user.followers_count #Int: number of people who follower the user

		# Store hashtags as comma seperated string
		hashtags = self.twitter_analyzer.store_hashtags(text)

		if hashtags:
			hashtags = ','.join(hashtags)

		# Clean text: Remove URLS, Hashtags and Username Handles
		text = self.twitter_analyzer.clean_text(text)

		#Get the sentiment score using VADER
		sentiment_score = self.twitter_analyzer.get_sentiment_score(text)
		neg_score = sentiment_score['neg']
		neu_score = sentiment_score['neu']
		pos_score = sentiment_score['pos']
		compound_score = sentiment_score['compound']

		### Print Statements for DEBUGGING ###
		# print("Text: " + text)
		# print("Score: {}".format(sentiment_score))
		# print("Hashtags: {}".format(hashtags))

		# # # Adding the Twitter Data into mySQL Database # # #
		self.database_manager.insert_data(id, created_at, author, text, retweet_count, favorite_count,
		neg_score, neu_score, pos_score, compound_score, hashtags, follower_count, search_words)

		# self.database_manager.debug()
		self.counter += 1

	def on_error(self, error_code):
		# Twitter API has rate limits, stop scraping data when warning is shown
		if error_code == 420:
			return False

class TwitterStreamer():
	def stream_tweets(self, search_words, num_tweets_to_grab = 20):

		#Handles Twitter Authentication and Connects to Twitter Streaming 
		l=search_words.split(',')
		#l.append(search_words)
		print("In class :",search_words,num_tweets_to_grab)
		listener = TwitterListener(num_tweets_to_grab)
		print("here 1:",search_words)	
		auth = tweepy.OAuthHandler(credentials.CONSUMER_KEY, credentials.CONSUMER_SECRET)
		auth.set_access_token(credentials.ACCESS_TOKEN, credentials.ACCESS_TOKEN_SECRET)
		stream = tweepy.Stream(auth, listener, tweet_mode = "extended")
		print("here 2 :",search_words)	
		# Filter Twitter Streams to capture data by the keywords:
		stream.filter(track = l, languages=["en"])
		print("here 3:",search_words)	
		

if __name__ == '__main__':
	
	twitter_streamer = TwitterStreamer()
	print(args.count)
	#print("In stremaer: ",search_words)
	twitter_streamer.stream_tweets(search_words,int(args.count))
