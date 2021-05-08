import os
import time
import tweepy
from flask import Flask, request, render_template, redirect, abort, flash, jsonify
from flask_cors import CORS, cross_origin  # This is the magic
from bson import json_util
import json
import pandas as pd
import psycopg2 as pg
import pandas.io.sql as psql
import datetime
from psycopg2.extras import RealDictCursor
import numpy as np
import networkx as nx
import re
from collections import Counter

app = Flask(__name__)   # create our flask app
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


def getIntForString(s):
    r = ''
    for c in s:
        r = r + str(ord(c))

    return r

def get_graph(hashtag_id):
    conn = pg.connect(dbname="platform", user="ps", password="ps@123", host="172.20.1.51", port="6011")
    cur = conn.cursor()
    
    df_text = pd.read_sql("select  c.*,b.sm_user_name,b.sm_screen_name,b.sm_location,b.sm_description,b.sm_follower_count,b.sm_following_count,b.sm_friends_count,b.sm_favourite_count,b.sm_status_count from (select sm_user_name source_sm_user_name,a.sm_user_id source_sm_user_id,a.sm_text,a.sm_hashtag_ids,a.sm_status_created_on,a.sm_target_user_ids, sm_screen_name source_sm_screen_name,sm_follower_count source_sm_follower_count, sm_following_count source_sm_following_count,sm_friends_count source_sm_friends_count,sm_favourite_count source_sm_favourite_count,sm_status_count source_sm_status_count from sm_status a INNER JOIN sm_user c ON c.id = a.sm_user_id where '"+hashtag_id+"' = ANY(a.sm_hashtag_ids) ) c  INNER JOIN sm_user b ON b.id = ANY( c.sm_target_user_ids)",con= conn)
    edges=list(zip(df1.source_sm_screen_name, df1.sm_screen_name))
    
    unique_pairs = {tuple(sorted(x)) for x in edges} 
    ntwrk=[]
    for pair in unique_pairs:
        b={"source_id" : getIntForString(pair[0]),"source" : pair[0],"destination_id" : getIntForString(pair[1]),"destination" : pair[1]}
        ntwrk.append(b)
    
    source_nodes=list(zip(df1.source_sm_screen_name, df1.source_sm_follower_count))
    target_nodes=list(zip(df1.sm_screen_name, df1.sm_follower_count))

    source_nodes.extend(target_nodes)
    all_nodes=list(set(source_nodes))

    my_dict=[]
    for n in all_nodes:
        b={'id': getIntForString(n[0]),'name':n[0],'size' : n[1]}
        my_dict.append(b)
    
    templateData = {
        'links' : ntwrk,
        'nodes' : my_dict
    }

    return(json.dumps(templateData,default=json_util.default))


@app.route('/social_media/link_analysis',methods=['GET','POST'])
@cross_origin()
def add_message():
    request.get_json(force=True)
    content = request.json
    records = None

    if content["hashtag"]:
        print(content["hashtag"])
        records = get_graph(content["hashtag"])
        return records
    else:
        return jsonify({})

app.debug = True
app.run(host='0.0.0.0', port=6021,debug=True)