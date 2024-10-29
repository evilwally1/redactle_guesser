
from html.parser import HTMLParser
import urllib.request as browser
import string
import time
import json
import re

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
# -M-A-I-N- -P-R-O-G-R-A-M-
#------------------------------------------------------------------------------
start_time_epoch  = time.time()
print('Started at '+ time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(start_time_epoch) ) )
wiki_atrical_urls   = get_wiki_article_urls()
total_artical_count = len(wiki_atrical_urls)
print( 'Total wiki article links found: '+ str(total_artical_count) )

# Write results out to file
out_fh = open( 'wiki_data.csv', 'w', encoding='utf-8' )

# See: https://www.mediawiki.org/wiki/API:Get_the_contents_of_a_page
wiki_text_url = 'https://en.wikipedia.org/w/api.php?action=query' \
                '&format=json' + '&prop=extracts' + '&exsentences=10' \
                '&exlimit=1'   + '&explaintext=1' + '&formatversion=2' \

processed_count = 0
for url in wiki_atrical_urls:
  processed_count = processed_count +1
  article_url = wiki_text_url +'&titles='+ url[6:]

  # Report on progress
  if processed_count % 100 == 0:
    report_time = time.strftime('%H:%M:%S', time.gmtime( time.time() ) )
    print(
      '{} Processed {:4} / {} or {:2.2%}'.format(
        report_time,
        processed_count,
        total_artical_count,
        processed_count/total_artical_count,
      )
    )
  
  # Try to get the wiki page details
  web_page = browser.urlopen( article_url )
  responce = json.loads( web_page.read().decode('utf8') )
  
  # Capture values from response
  page_id  = responce['query']['pages'][0]['pageid']
  title    = responce['query']['pages'][0]['title']
  extract  = responce['query']['pages'][0]['extract']

  # Write values out to file
  out_fh.write(
    '{:10},{:30},{:10},{:40},{}\n'.format(
      '"'+ str(page_id) +'"',
      '"'+ title +'"',
      '"'+ make_data_key(title) +'"',
      '"'+ url +'"',
      '"'+ str( make_data_keys(extract) ) +'"'
    )
  )

  if url == '/wiki/Amravati':
    break

print('Finished')
exit()
