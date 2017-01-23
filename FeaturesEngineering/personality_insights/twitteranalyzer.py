import sys
import requests
import json
import twitter
import config
import csv
import os
from StringIO import StringIO
out_dir='out'
if not os.path.exists(out_dir):
	os.makedirs(out_dir)


def flattenjson( b, delim ):
    val = {}
    for i in b.keys():
        if isinstance( b[i], dict ):
            get = flattenjson( b[i], delim )
            for j in get.keys():
                val[ i + delim + j ] = get[j]
        else:
            val[i] = b[i]
    return val


def export_insights_to_csv(fname, dc):
	input = map( lambda x: flattenjson(x,'__'), dc['tree']['children'] )
	columns = map( lambda x: x.keys(), input )
	columns = reduce( lambda x,y: x+y, columns )
	columns = list( set( columns ) )
	with open(out_dir+'/'+ fname, 'wb' ) as out_file:
	    csv_w = csv.writer( out_file )
	    csv_w.writerow( columns )
	    for i_r in input:
		csv_w.writerow( map( lambda x: i_r.get( x, "" ), columns ) )

def export_tweets(fname, tweets):
	with open(out_dir+'/'+fname,'w') as ft:
		for each in tweets:
			ft.write(each.text.encode('ascii','ignore')+'\n')

def convert_status_to_pi_content_item(s):
    # My code here
    return {
        'userid': str(s.user.id),
        'id': str(s.id),
        'sourceid': 'python-twitter',
        'contenttype': 'text/plain',
        'language': s.lang,
        'content': s.text,
        'created': s.created_at_in_seconds,
        'reply': (s.in_reply_to_status_id == None),
        'forward': False
    }

def analyze_tweets():
	twitter_api = twitter.Api(consumer_key=config.twitter_consumer_key,
				  consumer_secret=config.twitter_consumer_secret,
				  access_token_key=config.twitter_access_token,
				  access_token_secret=config.twitter_access_secret,
				  debugHTTP=True)

	insights={}
	tweets={}
	with open('twitter_handles.csv') as ft:
		for each in ft:
			name, handle=each.strip().split(',')
			if handle=='None' or handle=='none':
				continue
			try:
				statuses = twitter_api.GetUserTimeline(screen_name=handle, count=300)
				#print len(statuses)
				#pi_content_items_array = map(convert_status_to_pi_content_item, statuses)
				#pi_content_items = {'contentItems': pi_content_items_array}

				r = requests.post(config.pi_url + '/v2/profile?headers=True',
						  auth=(config.pi_username, config.pi_password),
						  headers={
						      'content-type': 'text/plain',
						      'Accept': 'text/csv'
						  },
						  data=' '.join(x for x in [y.text.encode('ascii','ignore') for y in statuses]))
						  

				#print("Profile Request sent. Status code: %d, content-type: %s" % (r.status_code, r.headers['content-type']))
				insights[name]=r.text
				tweets[name]=statuses
			except:
				pass

	return insights, tweets

def getFollowersCount():
        twitter_api = twitter.Api(consumer_key=config.twitter_consumer_key,
                                  consumer_secret=config.twitter_consumer_secret,
                                  access_token_key=config.twitter_access_token,
                                  access_token_secret=config.twitter_access_secret,
                                  debugHTTP=True)

        followers={}
        with open('twitter_handles.csv') as ft:
                for each in ft:
                        name, handle=each.strip().split(',')
                        if handle=='None' or handle=='none':
                                continue
                        try:
                                statuses = twitter_api.GetFollowersCount(screen_name=handle, total_count=200, include_user_entities=False)
                                count= len(statuses)
                                                      
                                tweets[name]=count
                        except:
                                pass

        return followers


if __name__=='__main__':
	insights, tweets=analyze_tweets()
	dfs=[]
	for k in insights:
		try:
			
			df2=pd.read_csv(StringIO(insights[k]))
			df2['celeb']=k
			dfs.append(df2)
			export_insights_to_csv(k+'.csv', insights[k])
		except:
			pass
	for k in tweets:
		try:
			export_tweets('tweets_'+k+'.csv', tweets[k])
		except:
			pass

	followers_count=getFollowersCount()
	with open('Followers_Count.csv','w') as fout:
		fout.write('Name,Count\n')
		for k,v in followers_count.items():
			four.write(str(k)+','+str(v)+'\n')

	df_merged=dfs[0]
	for i in range(1,len(dfs)):
		df_merged=df_merged.append(dfs[i])
	df_merged.to_csv('personality_insights_df.csv')
			
