import datetime
import mysql.connector
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly
import plotly.express as px
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd
from collections import Counter

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app1 = dash.Dash(__name__, external_stylesheets=external_stylesheets, requests_pathname_prefix='/app1/')


app1.layout = html.Div(children = [
		html.H2('Real-Time Twitter Sentiment Analysis for Analyzing Public Opinion',
			style = {'textAlign': 'center'}),
		html.H3('Currently Searching Twitter for the given Keyword {}'.format(""),
			style = {'textAlign': 'center'}),
		html.Div(id='live-update-graph-top'),
		html.Div(id='live-update-graph-bottom'),
		dcc.Interval(
			id = 'interval-component',
			interval = 1 * 60000,
			n_intervals = 0)
	], style = {'padding': '20px'})

def get_data():
	# Connect to the SQL database
	mydb = mysql.connector.connect(
				host = 'localhost',
				user = 'root',
				password = 'root',
				database = 'twitter_database'
			)

	# Use SQL query to get all tweets from the last 72 hrs
	time_now = datetime.datetime.utcnow()
	time_10mins_before = datetime.timedelta(hours=72,minutes=0)
	time_interval = time_now - time_10mins_before
	query = "SELECT * FROM tweets WHERE created_at >= '{}'".format(time_interval)
	df = pd.read_sql(query, con = mydb)
	return df

##### CALLBACKS #####
@app1.callback(Output('live-update-graph-top', 'children'),
	[Input('interval-component', 'n_intervals')])
def update_graph_top(n):
	df = get_data()

	# Assign positive, neutral or negative sentiment to each tweet
	df['sentiment'] = 0
	df.loc[df['compound_score'] >= 0.05, 'sentiment'] = 1
	df.loc[df['compound_score'] <= -0.05, 'sentiment'] = -1

	# Group the dataframe by time and sentiment per 5 second intervals
	result = df.groupby([pd.Grouper(key='created_at', freq='5s'), 'sentiment']).count().unstack(fill_value=0).stack().reset_index()
	# fig = px.line(result, x='created_at',y="id",color='sentiment')
	#print("hello")
	# Get the top hashtags used
	all_hashes = df.hashtags.values
	all_hashes = [item for item in all_hashes if item is not None]
	all_hashes = [x.lower() for item in all_hashes for x in item.split(',')]

	hashtag_counter = Counter(all_hashes)
	top_hashes = hashtag_counter.most_common()[:10]

	#Get the tweets from the people with most followers
	top_followers = df.sort_values(by='follower_count', ascending=False).iloc[:10]
	tweets_from_top_followers = top_followers.text.values
	author_top_followers = top_followers.author.values
	top_following_count = top_followers.follower_count.values


	# Create the graphs: Timeseries Graph and Pie Chart
	children = [
		html.Div([
			dcc.Graph(
					figure = {
						'data': [
							{
								'x' : result[result['sentiment'] == 0].created_at,
								'y' : result[result['sentiment'] == 0].id,
								'name': 'Neutral',
								'marker': {'color': 'rgb(131, 90, 241)'}
							},
							{
								'x' : result[result['sentiment'] == 1].created_at,
								'y' : result[result['sentiment'] == 1].id,
								'name' : 'Positive',
								'marker': {'color': 'rgb(255, 50, 50)'}
							},
							{
								'x' : result[result['sentiment'] == -1].created_at,
								'y' : result[result['sentiment'] == -1].id,
								'name' : 'Negative',
								'marker': {'color': 'rgb(184, 247, 212)'}
							}
						]
					}
				)], style = {'width': '73%', 'display': 'inline-block', 'padding': '0 0 0 20'}),
		html.Div([
			dcc.Graph(
					figure = {
						'data': [
							go.Pie(
									labels = ['Negative', 'Positive', 'Neutral'],
									values = [result[result['sentiment'] == -1].id.sum(),
										result[result['sentiment'] == 1].id.sum(),
										result[result['sentiment'] == 0].id.sum()],
									name = 'pieChart',
									marker_colors = ['rgb(184, 247, 212)','rgb(255, 50, 50)','rgb(131, 90, 241)'],
								)
						]
					}
				)], style = {'width': '27%', 'display': 'inline-block'}),
		html.Div([
			dcc.Graph(
					figure = {
						'data': [
							go.Bar(
									x = [item[1] for item in top_hashes][::-1],
									y = [item[0] for item in top_hashes][::-1],
									orientation = 'h'
								)
						],
						'layout': {
							'title': 'Most Used Hashtags in the Last 24 hours',
							'xaxis': {'automargin': True},
							'yaxis': {'automargin': True}
						}
					}
				)], style = {'width': '45%', 'display': 'inline-block'}),
		html.Div([
			dcc.Graph(
					figure = {
						'data': [
							go.Table(
									header = {
										'values': ['Username', 'Tweet', 'Follower Count'],
										'align': 'left',
										'fill_color': 'rgb(107,174,214)',
										'font': {'size': 15}
									},
									cells = {
										'values': [author_top_followers, tweets_from_top_followers, top_following_count],
										'align': 'left',
										'fill_color': 'rgb(189, 215, 231)'
									})
						],
						'layout': {
							'title': 'Tweets from Users with Most Followers',
							'xaxis': {'automargin': True},
							'yaxis': {'automargin': True}
						}

					}
				)], style = {'width': '55%', 'display': 'inline-block'})
	]
	return children


if __name__ == '__main__':
    app.run_server(debug=True)




