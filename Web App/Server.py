import os
from flask import  Flask, request, render_template, g, redirect, Response, url_for, session
import tweepy as tw
import preprocessor as p
from preprocessor import clean, tokenize, parse, set_options
import pandas as pd
import re #regular expression
from textblob import TextBlob
import string
import nltk
from nltk.tokenize import word_tokenize
#nltk.download('punkt')
from pytrends.request import TrendReq
import matplotlib
from matplotlib import pyplot as plt
#from werkzeug import secure_filename
pytrend = TrendReq(hl='en-US', tz=360)

auth = tw.OAuthHandler(
'8Uslx3y5TBcs1BoPGlpPjYzc8', 
'mC9SZZEccIdODx2XUdsXyBlk5kCj18aHoqTftyjiJ2AfCdhGoA')
auth.set_access_token('937889022969597952-2PV3S06eXNylx8DVmEnrU2zlGWO0aby', 
                      '8sHKZU37LpawZEwoGJAALsvPSrbYIsYZmKYKjrEBbvXAB')
api = tw.API(auth, wait_on_rate_limit=True)

def clean_tweet_single(s):
    s=p.clean(str(s))
    s1=s.replace('"b','')
    s2=s1.replace('b"','')
    s3=re.sub('x[a-z0-9][a-z0-9]','',s2)
    s4=s3.replace('\\n','')
    s5=s4.replace('&amp;','')
    s6=s5.translate(str.maketrans('', '', string.punctuation))
    s_clean=re.sub(' +', ' ',s6 )
    return(s_clean)

def clean_tweet(ls):
    s=''
    for i in ls:
        s=s+p.clean(str(i))
    s1=s.replace('"b','')
    s2=s1.replace('b"','')
    s3=re.sub('x[a-z0-9][a-z0-9]','',s2)
    s4=s3.replace('\\n','')
    s5=s4.replace('&amp;','')
    s6=s5.translate(str.maketrans('', '', string.punctuation))
    s_clean=re.sub(' +', ' ',s6 )
    #return(s_clean)
    return (TextBlob(s_clean).sentiment.polarity)

def sl_single(sn):
    pytrend.build_payload(kw_list=[sn])
    related_topic = pytrend.related_topics()
    p = related_topic[sn]['top']
    related = p[['topic_title','topic_type']]
    kg=[]
    for i in related.index:
        if ('band' in related['topic_type'][i] or 
            'Band' in related['topic_type'][i] or 
            'Supergroup' in related['topic_type'][i]):
            kg.append(related['topic_title'][i])
    #print(kg)
    userid=[]
    name=[]
    screenName=[]
    location=[]
    if (len(kg) > 3):
        n = 200
    else:
        n = 300
    for k in kg:
        search_word = k+' OR '+k.replace(" ", "")
        tweets = tw.Cursor(api.search, q=search_word+ " -filter:retweets", lang="en").items(n)
        for tweet in tweets:
            s=clean_tweet_single(tweet.text)
            if(TextBlob(s).sentiment.polarity > 0):
                if ('New York' in tweet.user.location or 'NY' in tweet.user.location):
                    userid.append(tweet.user.id)
                    name.append(tweet.user.name)
                    screenName.append(tweet.user.screen_name)
                    location.append(tweet.user.location)
                else:
                    pass
            else:
                pass
    userInfo=pd.DataFrame({'Performer':[sn]*len(userid),'UserID':userid,
                       'Name':name,'ScreenName':screenName,'Location':location})
    userInfo.drop_duplicates(keep='first',inplace=True) 
    return(userInfo)


popular=['PalayeRoyale', 'Microwave', 'PearlJam','VERITE','Tyr','Subhumans','Cold','H2O','Tool','Accept',
         'Juice','AlterBridge','Elder','TheTemptations','TheMachine','Snot','TheGoodLife','TheLumineers','Starset',
         'Primus','Bauhaus', 'NileRodgers','Failure','RageAgainstTheMachine','Disturbed','D.R.I.','JudasPriest',
         'Nightwish','EzraFurman','Everlast']

def get_singer_List(popular, n):
    pol=[]
    for i in popular:
        df = pd.read_csv('/Users/kexinsu/Desktop/哥大/6895/singer/'+ i +'.csv',header=None)
        df_ls = df.values.tolist()
        pol.append(clean_tweet(df_ls))
    popular=pd.DataFrame(popular)
    pol=pd.DataFrame(pol)

    polar = pd.concat([popular, pol], axis=1, ignore_index=True)

    polar.sort_values(by=[1], inplace=True, ascending=False,ignore_index=True)
    #print(polar)
    final_singer=list()
    i=0
    while i<n:
        sp = re.sub(r"(\w)([A-Z])", r"\1 \2", polar[0][i])
        final_singer.append(sp)
        i+=1
    singer_fin=pd.DataFrame({'Singer Name':final_singer, 'Polarity Score':polar[0:n][1]})
    return(singer_fin)



app = Flask(__name__)    
        
@app.route("/")
def home():
    return render_template('home.html')


@app.route("/concertSelection", methods=['GET', 'POST'])
def conSelect():
    if request.method == 'POST' and 'num' in request.form:
        #file = request.files['file']
        num = request.form['num']
        df = get_singer_List(popular, int(num))
        return render_template("conSelection.html", tables=[df.to_html(classes='data')],
                               titles=df.columns.values)
    else:
        return render_template("conSelection.html")

 
@app.route("/allSinger", methods=['GET', 'POST'])
def allSinger():
    if request.method == 'POST' and request.form['name1']=='Palaye Royale' and request.form['name2']=='':
        df = pd.read_csv('/Users/kexinsu/Desktop/哥大/6895/app/PRbuyerInfo.csv')
        return render_template("singleSinger.html", tables=[df.to_html(classes='data')], titles=df.columns.values)
    elif request.method == 'POST' and request.form['name1']=='Nile Rodgers':
        df = pd.read_csv('/Users/kexinsu/Desktop/哥大/6895/app/NRbuyerInfo.csv')
        return render_template("singleSinger.html", tables=[df.to_html(classes='data')], titles=df.columns.values) 
    elif request.method == 'POST' and request.form['name4']!='' and request.form['name5']!='':
        df = pd.read_csv('/Users/kexinsu/Desktop/哥大/6895/app/buyerInfoAll.csv')
        return render_template("singleSinger.html", tables=[df.to_html(classes='data')], titles=df.columns.values)
    elif request.method == 'POST' and request.form['name3']!='':
        df = pd.read_csv('/Users/kexinsu/Desktop/哥大/6895/app/buyerInfo3.csv')
        return render_template("singleSinger.html", tables=[df.to_html(classes='data')], titles=df.columns.values)
    else:
        return render_template("singleSinger.html")
        
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000, debug=True)
