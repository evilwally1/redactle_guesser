
from html.parser import HTMLParser
import urllib.request as browser
import string
import time
import json
import re

import threading
import sqlite3

#------------------------------------------------------------------------------
# CLASS: WikiParser
#------------------------------------------------------------------------------
class wikiParser( HTMLParser ):
    
  def __init__(self, *, convert_charrefs=True):
    self.convert_charrefs = convert_charrefs
    self.reset()
    self.links = []
    return
  
  def process( self, url ):
    self.url = url
    self.links = []
    page = browser.urlopen( url )
    html = page.read().decode('utf8')
    self.feed(html)

    # Convert to dictionary to remove duplicate links
    all_links = {}
    for link in self.links:
      
      # remove links without text
      if 'text' not in link:
        continue
      
      thing = 'sometext'

      # remove links not to wiki
      if not link['url'].startswith('/wiki/'):
        continue
      
      # remove links to unwanted things
      if link['url'] == '/wiki/Main_Page':
        continue
      if link['url'].startswith('/wiki/File:'):
        continue
      if link['url'].startswith('/wiki/User:'):
        continue
      if link['url'].startswith('/wiki/Wikipedia_talk:'):
        continue
      if link['url'].find(':') > 0 and link['url'].find('/Level/') == -1:
        continue
      all_links[ link['url'] ] = link['text']

    return all_links

  def handle_starttag(self, tag, attrs):
    if tag == "a":
      for att in attrs:
        # Grab just the href link attribute
        if att[0] == 'href':
          self.links.append( { 'url': att[1] } )
    return

  def handle_data(self, data):
    # Skip blank data fields
    if not data.isspace():
      return
    
    # Check if any links have been found
    if len(self.links) == 0:
      return
    
    # Already set text on last link
    if 'text' in self.links[-1]:
        return
    
    # Set text on last link
    self.links[-1]['text'] = data
    return

#------------------------------------------------------------------------------
def get_wiki_article_urls():
  base_url   = 'https://en.wikipedia.org'
  wiki_atrical_urls = {}
  
  # Start at page 4 as it contains links to all the things we want
  parser = wikiParser()
  url    = base_url +'/wiki/Wikipedia:Vital_articles/Level/4'
  level_4_links = parser.process( url )

  # Check wiki links from page 4 for other articles
  for link in sorted( level_4_links ):

    # Skip links not to 'level' articles
    if not link.startswith('/wiki/Wikipedia:Vital_articles/Level/'):
      wiki_atrical_urls[ link ] = 1

    # Get links from sub pages 
    level_count = 0
    for sub_link in sorted(  parser.process( base_url + link ) ):

      # Skip links not to 'level' articles
      if sub_link.startswith('/wiki/Wikipedia:Vital_articles/Level/'):
        continue

      # Capture article link and count it and 
      wiki_atrical_urls[ sub_link ] = 1
      level_count = level_count +1

    # Report on number of articles found under 
    print( '{:-4} links found from URL:{}'. format( level_count, base_url + link ) )

  return wiki_atrical_urls

#------------------------------------------------------------------------------
def make_data_key( text ):
  keys = []
  text = re.sub( r'[^\w\s]', ' ', text )
  text = ' '.join( text.split() )
  words = re.split( r'[\s]', text )
  for word in words:
    keys.append( str( len( word.strip() ) ) )
  return '-'.join( keys )

#------------------------------------------------------------------------------
def make_data_keys( text ):
  keys = []
  for sentence in text.split('. '):
    keys.append( make_data_key(sentence.strip()) )
  return keys

#------------------------------------------------------------------------------
def prep_database( cur, con ):
  
  # Ensure table exist
  res = cur.execute("SELECT name FROM sqlite_master WHERE name='articles'")
  if res.fetchone() is None:
    cur.execute("CREATE TABLE articles( url, id, title, title_key, word_keys)")
    print('Table created')
  else:
    print('Table exists')
  
  # Bail if the table already has records
  res = cur.execute("SELECT count(*) FROM articles")
  record_count = res.fetchone()[0]
  if record_count > 40000:
    print("Found {} articles in the local DB".format( record_count ) )
    print("No need to add more articles")
    return
  
  # Get all the article links to add to the table
  print("Finding atricles to add to DB")
  wiki_atrical_urls   = get_wiki_article_urls()
  total_artical_count = len(wiki_atrical_urls)
  print( 'Total wiki article links found: '+ str(total_artical_count) )
  
  # Convert list to list of tuples for the executemany function
  links = []
  for url in sorted(wiki_atrical_urls):
    links.append( (url,) )

  # Add article links to the table
  print('Adding links to DB')
  cur.executemany("INSERT INTO articles( url ) VALUES (?)", links )
  con.commit()

  # Report on records started
  res = cur.execute("SELECT count(*) FROM articles")
  record_count = str(res.fetchone()[0])
  print("Found {} articles in the local DB".format( record_count ) )

  return

#------------------------------------------------------------------------------
def process_article( url ):
  # See: https://www.mediawiki.org/wiki/API:Get_the_contents_of_a_page
  wiki_text_url = 'https://en.wikipedia.org/w/api.php?action=query' \
                  '&format=json' + '&prop=extracts' + '&exsentences=10' \
                  '&exlimit=1'   + '&explaintext=1' + '&formatversion=2'

  article_url = wiki_text_url +'&titles='+ url[6:]

  # Try to get the wiki page details
  web_page = browser.urlopen( article_url )
  responce = json.loads( web_page.read().decode('utf8') )
  
  # Capture values from response
  page_id   = responce['query']['pages'][0]['pageid']
  title     = responce['query']['pages'][0]['title']
  extract   = responce['query']['pages'][0]['extract']
  title_key = make_data_key(title)
  words_key = str( make_data_keys(extract) )
  
  # Update the record
  parms = (  page_id, title, title_key, words_key, url )
  db_con = sqlite3.connect("wiki_data.db")
  db_cur = db_con.cursor()
  db_cur.execute( "Update articles set id=?, title=?, title_key=?, word_keys=? where url=?", parms )
  db_con.commit()

  # Report on updated record
  #data = db_cur.execute("SELECT url, id, title_key FROM articles where url=?", (url,) ).fetchall()
  #print( 'Updated to: '+ str(data) )
  return

#------------------------------------------------------------------------------
# -M-A-I-N- -P-R-O-G-R-A-M-
#------------------------------------------------------------------------------
print('Started at '+ time.strftime('%H:%M:%S', time.gmtime( time.time() ) ) )

# Open local DB file
db_con = sqlite3.connect("wiki_data.db")
db_cur = db_con.cursor()
prep_database( db_cur, db_con )

# Process each article
data_to_check = db_cur.execute("SELECT * FROM articles where id is null order by url").fetchall()
print( 'Records to update: '+ str( len(data_to_check) ) )

run_limit = 20

# Loop till all data is processed
while len(data_to_check) > 0:

  # If we are already running enough threads, wait a sec
  if len(threading.enumerate()) >= run_limit:
    #time.sleep(1)
    continue
  
  # Take the next url and create a new thread to process it
  url = data_to_check.pop(0)[0]
  print( 'process_article( '+ url +' )' )
  new_thread = threading.Thread(target=process_article, args=(url,) )
  new_thread.start()

print('Finished')
exit()
