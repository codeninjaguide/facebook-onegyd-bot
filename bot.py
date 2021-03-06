import requests
from bs4 import BeautifulSoup
import time
import facebook
import threading
from flask import Flask
import waitress
import os
import json

#app
app = Flask(__name__)

#VARIABLES
GDRIVEURL = os.environ.get('GDRIVEURL')
SITE = os.environ.get('SITE')
FB_ACCESS_TOKEN = os.environ.get('FB_ACCESS_TOKEN')

#Fetch all the data from Google Sheet
def GoogleSheetDB():
    post_url = "{}?type=get".format(GDRIVEURL)
    data = list()
    db_list = requests.get(post_url).json()
    for item in db_list:
        data.append(item)
    return data
    
def InsertToGoogleSheet(link):
    post_url = "{}?type=put&link={}".format(GDRIVEURL, link)
    try:
        requests.get(post_url)
    except:
        return None

#Scrape data from onegyd post-sitemap.xml
def ScrapeSitemapXml():
    SCRAPED_XML = list()
    soup = BeautifulSoup(requests.get(SITE).text, 'html.parser')
    for loc in soup.select('url > loc'):
        SCRAPED_XML.append(loc.text)  
    return SCRAPED_XML

#UpdateFacebookPost
def updateFacebookPost(m, l):
    try:
        graph = facebook.GraphAPI(FB_ACCESS_TOKEN)
        graph.put_object(
            parent_object="me",
            connection_name="feed",
            message=m,
            link=l
        )
    except:
        return None

#Meta description scraping
def ScrapeMetaContent(link):
    soup = BeautifulSoup(requests.get(link).text, 'html.parser')
    desc = soup.find("meta",  property="og:description")
    desc_data = desc["content"] if desc else "No meta title given"
    return desc_data

#Main Function
def main():
    new_post = list()
    a = GoogleSheetDB()
    b = ScrapeSitemapXml()
    
    for item in b:
        if not item in a:
            #print(item)
            #print("new post")
            meta_description = ScrapeMetaContent(item)
            new_post.append({
                "link": item,
                "meta_description": meta_description
            })
    
    if len(new_post) > 0:  
        for item in new_post:
            # print(item['link'])
            # print(item['meta_description'])
            s = updateFacebookPost(item['meta_description'], item['link'])
            InsertToGoogleSheet(item['link'])
    print("Main Thread Completed...")
    return


@app.route("/")
def index():
    th = threading.Thread(target=main)
    th.start()
    return json.dumps({
        "Status": 200,
        "message": "{} Thread Started...".format(threading.current_thread().ident)
    })

if __name__ == "__main__":
    app.debug = False
    port = int(os.environ.get('PORT', 33507))
    waitress.serve(app, port=port)
