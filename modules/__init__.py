from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from dash import Dash
from modules.app1 import app1
from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.serving import run_simple
import dash_html_components as html
import pyrebase
from twilio.twiml.messaging_response import MessagingResponse
from textblob import TextBlob
import tweepy


app = Flask(__name__)
config = {
  'apiKey': "AIzaSyAqOXRxDJOKUan58XZXnv7wHZ62jav6gKo",
  'authDomain': "dbd-project-48733.firebaseapp.com",
  'projectId': "dbd-project-48733",
  'databaseURL':"https://dbd-project-48733-default-rtdb.europe-west1.firebasedatabase.app/",
  'storageBucket': "dbd-project-48733.appspot.com",
  'messagingSenderId': "599766163003",
  'appId': "1:599766163003:web:7deb49a214969bebbcc61e",
  'measurementId': "G-DW075HEN5F"
}
#initialize firebase
firebase = pyrebase.initialize_app(config)
auth = firebase.auth()
db = firebase.database()

#Tweepy api for Whatsapp bot

CONSUMER_KEY = 'enUKRffwxqZW6aoJDuIkku9xN'
CONSUMER_SECRET = 'eSg94gDpNcZLxTkSqJiS2dGP9jwK9cHS0XZ2W9NAxVeoDRRU89'
ACCESS_TOKEN = '1372516587232653312-ebg0MzRW8D1aYvshsCUA1ZTflFHowJ'
ACCESS_TOKEN_SECRET = 'sLIQpz5BScPklOeqK14YuxKwP3MhKQ9NR4TjakgWAINlU'
# create OAuthHandler object
auth1 = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
# set access token and secret
auth1.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
# create tweepy API object to fetch tweets
api = tweepy.API(auth1)


app.config['SECRET_KEY'] = '4YrzfpQ4kGXjuP6w'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:root@127.0.0.1:3306/crud_twitterdb'
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'home'




from modules import routes

app = DispatcherMiddleware(app, {
    '/app1': app1.server
})
run_simple('127.0.0.1',5000,app,use_reloader=True,use_debugger=True)