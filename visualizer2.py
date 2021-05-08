#!/usr/bin/env python

import json_lines
import streamlit as st
import os
import numpy as np
import altair as alt
import pandas as pd
from src.transformations import *
from src.networks import *
from src.utils import *
from datetime import datetime
import datetime as dt


# ------- UI --------- #
# Some CSS changes
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;\
            700&display=swap" rel="stylesheet"> ',
            unsafe_allow_html=True)
st.markdown(
    '<style>.reportview-container .markdown-text-container{font-family:\
    "Inter", -apple-system,system-ui,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica\
     Neue",Arial,sans-serif}\
     #titlelink {color: white;\
     text-decoration: none}\
     #titlelink:hover {color: #cccccc;\
     text-decoration: none}</style>', unsafe_allow_html=True)
st.markdown('<style>.ae{font-family:"Inter",-apple-system,system-ui,BlinkMacSystemFont,\
            "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}</style>',
            unsafe_allow_html=True)
st.markdown('<style>body{font-family:"Inter",-apple-system,system-ui,BlinkMacSystemFont,\
            "Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}</style>',
            unsafe_allow_html=True)
st.markdown('<style>code{color:black}</style>', unsafe_allow_html=True)
st.markdown('<style>.reportview-container .markdown-text-container a{color:rgba\
            (83,106,160,1)}</style>', unsafe_allow_html=True)
st.markdown('<head><title>twitter explorer</title></head>',
            unsafe_allow_html=True)
st.markdown('<p style="font-size: 30pt; font-weight: bold; color: white; \
    background-color: #000">&nbsp;\
    <a id="titlelink" href="https://twitterexplorer.org">twitter explorer\
    </p>', unsafe_allow_html=True)
st.title("Visualizer")

def file_selector(folder_path='.'):
    try:
        filenames = os.listdir(folder_path)
    except FileNotFoundError:
        st.error("The `./data` folder does not exist. Please create it and insert \
                your Twitter collections in jsonl format.")
    if '.DS_Store' in filenames:
        filenames.remove('.DS_Store')
    filenames = list(reversed(filenames))
    selected_filename = st.selectbox(
        'Select a tweet collection inside ./data', filenames)
    return os.path.join(folder_path, selected_filename)

filename = file_selector('./data')
filesize = os.path.getsize(filename) >> 20

if filename[-1] == "l":
    subtitlevalue = filename[25:][:-6]
else:
    subtitlevalue = filename[25:][:-5]

collectedon = filename[7:17]
subtitle = subtitlevalue
project = st.text_input(label="Set a foldername for the project that will be \
    created in ./output",
                        value=f"{collectedon}_{subtitle}")

st.write(f'`You selected {filename}.`<br>`\
    The file size is about {filesize}MB.`', unsafe_allow_html=True)

datadir = "./data/"
outputdir = "./output/"
projectdir = outputdir + project

st.write("---")

st.header("Timeline of tweets")

#st.write("Plot the amount of tweets over time.")
if st.button("Plot tweet count over time"):

    # legacy dataset conversion
    if filename[-1] == "n":
        with st.spinner("You are trying to load a legacy dataset. Converting \
                        dataset to jsonl and saving..."):
            json_to_jsonl(filename)
        filename += "l"
    
    with st.spinner("Reading file..."):
        tweetdf = tweetjson_to_df(filename)
        grouped_df = groupby_dates(tweetdf)
        
        ot_count = int(sum(grouped_df["original tweets"]))
        rt_count = int(sum(grouped_df["retweets"]))
        tt_count = ot_count+rt_count
        
        if rt_count < ot_count:
            plots = plot(grouped_df, ["original tweets", "retweets"])
        else:
            plots = plot(grouped_df, ["retweets", "original tweets"])

        st.altair_chart(plots, use_container_width=True)
        
        firstdate_str = str(list(tweetdf.iloc[[-1]]["time"])[0])[:16]
        lastdate_str = str(list(tweetdf.iloc[[0]]["time"])[0])[:16]

        st.write(f"The dataset contains {tt_count} tweets, from which {ot_count} are\
                   original tweets and {rt_count} are retweets.")
        st.write(f"The first tweet is from {firstdate_str}, the last tweet is from \
        {lastdate_str} (UTC).")

        if not os.path.exists(projectdir):
            os.makedirs(projectdir)

        plots.save(f"{projectdir}/{project}_timeline.html")

st.write("---")

# -------------------------------------------------------------------

st.header("Interactive networks")

st.write("Create interaction networks (retweet networks) and semantic networks \
    (hashtag networks). Only retweets from this time range will be used to create\
     the networks.")


# guess the default daterange from the filename
try:
    today = dt.date.fromisoformat(filename[7:17])
    lastweek = today + dt.timedelta(days=-8)
except ValueError:
    today = dt.date.today()
    lastweek = today + dt.timedelta(days=-8)

daterange = st.date_input(label="Timerange for creating networks:",
                          value=[lastweek,
                                 today])

st.write("---")

st.subheader("Retweet Network")
st.write()
st.write("Directed network in which nodes are users. A link is drawn from \
    `i` to `j` if `i` retweets `j`.")
st.write('<span style="text-decoration: underline;">Options</span>', 
         unsafe_allow_html=True)
rtn_giantcomponent = st.checkbox("Giant component", key='rtn_giantcomponent')
privacy = st.checkbox(
    "Remove metadata of nodes that are not public figures \
     (less than 5000 followers)")
st.write('<span style="text-decoration: underline;">Aggregation method</span>', 
         unsafe_allow_html=True)

rtn_aggregation_soft = st.checkbox(
    "Soft aggregate (remove nodes with in-degree 0 and only one neighbor)",
    key='rtn_aggregation_soft')
rtn_aggregation_hard = st.checkbox(
    "Hard aggregate (remove nodes with in-degree ≤ threshold)",
    key='rtn_aggregation_hard')
threshold = 0
if rtn_aggregation_hard:
    thresh_rtn = st.slider("threshold", 0.0, 20.0, 1.0, 1.0, key='thresh_rtn')
    threshold += thresh_rtn
if rtn_aggregation_soft:
    aggregationmethod = 'soft'
elif rtn_aggregation_hard:
    aggregationmethod = 'hard'
else:
    aggregationmethod = None

rtn_comdeclist = []
st.write('<span style="text-decoration: underline;">Community detection</span>', 
         unsafe_allow_html=True)
rtn_louvain = st.checkbox("Louvain", key='rtn_louvain')
if rtn_louvain:
    rtn_comdeclist.append("louvain")
rtn_infomap = st.checkbox("Infomap", key='rtn_infomap')
if rtn_infomap:
    rtn_comdeclist.append("infomap")

if st.button("Generate Retweet Network"):
    if not os.path.exists(projectdir):
        os.makedirs(projectdir)
    # load the tweets
    # legacy dataset conversion
    if filename[-1] == "n":
        with st.spinner("You are trying to load a legacy dataset. Converting \
                        dataset to jsonl and saving..."):
            json_to_jsonl(filename)
        filename += "l"
    
    # return error when trying to choose both aggregations
    if rtn_aggregation_soft is True and rtn_aggregation_hard is True:
        st.error("Please choose only one of the aggregations")

    with st.spinner("Creating retweet network..."):
        G = retweetnetwork(filename=filename,
                           giant_component=rtn_giantcomponent,
                           aggregation=aggregationmethod,
                           t=threshold,
                           starttime=daterange[0],
                           endtime=daterange[1])
        if privacy:
            G = makeprivate(G)

    # get the first and last tweet    
    edgeslist = list(G.es)
    #st.write(len(edgeslist))
    firstdate_str = iso_to_string(edgeslist[-1]["time"])
    lastdate_str = iso_to_string(edgeslist[0]["time"])

    if "louvain" in rtn_comdeclist:
        with st.spinner("Computing Louvain communities..."):
            G, cgl = compute_louvain(G)
            cgl_d3 = d3_cg_rtn(cgl)
            cgl_d3["graph"] = {}
            cgl_d3['graph']['type'] = "Retweet network <br> Louvain graph"
            cgl_d3['graph']['keyword'] = subtitle
            cgl_d3['graph']['collected_on'] = collectedon
            cgl_d3['graph']['first_tweet'] = firstdate_str
            cgl_d3['graph']['last_tweet'] = lastdate_str
            cgl_d3['graph']['N_nodes'] = len(cgl_d3["nodes"])
            cgl_d3['graph']['N_links'] = len(cgl_d3["links"])
            x = cg_rtn_html(cgl_d3)
            with open(f"{projectdir}/{project}_RTN_CG_louvain.html", "w",
                      encoding='utf-8') as f:
                f.write(x)

    if "infomap" in rtn_comdeclist:
        with st.spinner("Computing InfoMap communities..."):
            G = compute_infomap(G)

    # create d3-graph and fill it with info
    RTN = d3_rtn(G)
    RTN['graph'] = {}
    RTN['graph']['type'] = "Retweet network"
    RTN['graph']['N_nodes'] = len(RTN["nodes"])
    RTN['graph']['N_links'] = len(RTN["links"])
    RTN['graph']['keyword'] = subtitle
    RTN['graph']['collected_on'] = collectedon
    RTN['graph']['first_tweet'] = firstdate_str
    RTN['graph']['last_tweet'] = lastdate_str

    if privacy:
        x = rtn_html_p(data=RTN)
    else:
        x = rtn_html(data=RTN)
    with st.spinner("Writing html..."):
        with open(f"{projectdir}/{project}_RTN.html", "w",
                  encoding='utf-8') as f:
            f.write(x)

    savename = f"{projectdir}/{project}_RTN"
    exportname = f"{projectdir}/export/"
    if not os.path.exists(exportname):
        os.makedirs(exportname)
    convert_graph(G, exportname + project + "_RTN")

    N_edges = len(RTN["links"])

    if N_edges > 1e5:
        st.warning("The network you are trying to visualize has \
                  more than 10,000 links. Consider using a stronger\
                  aggregation method if the interactive visualization is\
                  unresponsive.")
    
    st.success(f"`Saved the interactive retweet network to: {savename}.html`.")
    if len(rtn_comdeclist) != 0:
        st.success(f"`Saved the cluster graphs to: {savename}_CG.html`.")
    st.success(f"`Exported the network as gml (.gml), edgelist (.csv) and\
               dot (.gv) to: \n {exportname}`.")

# ------------------------------------------------------------------
st.write("---")

st.subheader("Hashtag Network")
st.write("Undirected network in which nodes are hashtags. \
    A link is drawn between `i` and `j` if they appear in the same tweet.")
st.write('<span style="text-decoration: underline;">Options</span>', 
         unsafe_allow_html=True)
htn_giantcomponent = st.checkbox("Giant component", key='htn_giantcomponent')

advanced = st.checkbox("Advanced node / link removal thresholds")
node_thresh_htn = 0
link_thresh_htn = 0
if advanced:
    node_thresh_htn = st.slider("Remove hashtags that appear less than x times", 0.0, 100.0, 1.0, 1.0, key='n_thresh_htn')
    link_thresh_htn = st.slider("Remove edges that link hashtags less than than x times", 0.0, 50.0, 1.0, 1.0, key='l_thresh_htn')

st.write('<span style="text-decoration: underline;">Community detection</span>', 
         unsafe_allow_html=True)
htn_louvain = st.checkbox("Louvain", key='htn_louvain')
if st.button("Generate Hashtag Network"):
    if not os.path.exists(projectdir):
        os.makedirs(projectdir)
    # legacy dataset conversion
    if filename[-1] == "n":
        st.warning(
            "You are trying to load a legacy dataset. \
            Converting dataset to jsonl and saving...")
        json_to_jsonl(filename)
        filename += "l"
    # load the tweets
    with st.spinner("Loading tweets..."):
        with open(filename, "rb") as f:
            firstline = f.readline()
            f.seek(-2, os.SEEK_END)
            while f.read(1) != b"\n":
                f.seek(-2, os.SEEK_CUR)
            lastline = f.readline()
        firstdate = json.loads(lastline)["created_at"]
        lastdate = json.loads(firstline)["created_at"]
        firstdate_str = firstdate[:16]
        lastdate_str = lastdate[:16]
    with st.spinner("Creating hashtag network..."):
        H = hashtagnetwork(filename=filename,
                           giant_component=htn_giantcomponent,
                           node_threshold=node_thresh_htn,
                           link_threshold=link_thresh_htn,
                           starttime=daterange[0],
                           endtime=daterange[1])
    if htn_louvain:
        with st.spinner("Computing communities..."):
            H, Hcg = compute_louvain(H)
            cgl_d3 = d3_cg_htn(Hcg)
            cgl_d3["graph"] = {}
            cgl_d3['graph']['type'] = "Hashtag network <br> Louvain graph"
            cgl_d3['graph']['keyword'] = subtitle
            cgl_d3['graph']['collected_on'] = collectedon
            cgl_d3['graph']['first_tweet'] = firstdate_str
            cgl_d3['graph']['last_tweet'] = lastdate_str
            cgl_d3['graph']['N_nodes'] = len(cgl_d3["nodes"])
            cgl_d3['graph']['N_links'] = len(cgl_d3["links"])
            x = cg_htn_html(cgl_d3)
            with open(f"{projectdir}/{project}_HTN_CG_louvain.html",
                      "w", encoding='utf-8') as f:
                f.write(x)

    # get the first and last tweet    
    edgeslist = list(H.es)
    firstdate_str = iso_to_string(edgeslist[-1]["time"])
    lastdate_str = iso_to_string(edgeslist[0]["time"])

    HTN = d3_htn(H)
    HTN['graph'] = {}
    HTN['graph']['type'] = "Hashtag network"
    HTN['graph']['N_nodes'] = len(HTN["nodes"])
    HTN['graph']['N_links'] = len(HTN["links"])
    HTN['graph']['keyword'] = subtitle
    HTN['graph']['collected_on'] = collectedon
    HTN['graph']['first_tweet'] = firstdate_str
    HTN['graph']['last_tweet'] = lastdate_str

    x = htn_html(data=HTN)
    with st.spinner("Writing html..."):
        with open(f"{projectdir}/{project}_nt{node_thresh_htn}_lt{link_thresh_htn}_HTN.html", "w", encoding='utf-8') as f:
            f.write(x)

    savename = f"{projectdir}/{project}_nt{node_thresh_htn}_lt{link_thresh_htn}_HTN"
    exportname = f"{projectdir}/export/"
    if not os.path.exists(exportname):
        os.makedirs(exportname)
    convert_graph(H, exportname + project + "_HTN")

    st.success(f"`Saved the interactive hashtag network as to: {savename}.html`.")
    if htn_louvain:
        st.success(f"`Saved the cluster graph to: {savename}_CG.html`.")
    st.success(f"`Exported the network as graphml (.gml), edgelist (.csv) and\
               dot (.gv) to: \n {exportname}`.")
