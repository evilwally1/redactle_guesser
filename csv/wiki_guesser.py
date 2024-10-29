import csv
import re
import argparse

#------------------------------------------------------------------------------
def parse_inputs():
  ap = argparse.ArgumentParser()
  ap.add_argument( "-df", "--data_file", required=False,  help="Data file to use", default='wiki_data_V1.csv')
  ap.add_argument( "-t", "--title",      required=True,   help="Title copied from Redactle")
  ap.add_argument( "-w", "--words",      required=True,   help="Words copied from Redactle")
  args = vars( ap.parse_args() )
  return ( args['data_file'], args['title'], args['words'] )

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
( data_file, input_title, input_words ) = parse_inputs()

# Read results out to file
in_fh = open( data_file, 'r', encoding='utf-8' )
csv_fh = csv.reader( in_fh )

input_title_key = make_data_key( input_title.replace('█','x') )
input_words_key = make_data_key( input_words.replace('█','x') )

print( 'Title Key:'+ input_title_key )
print( 'Words Key:'+ input_words_key )

# Check every record in the file
summary_count = 0
for record in csv_fh:
  
  # Split the record into the values we want
  ( wiki_id, title, title_key, url, sentence_keys ) = record
  title         = title.strip()
  title_key     = title_key.strip()
  sentence_keys = sentence_keys.strip()

  # Skip things where the title don't match the key
  if title_key != input_title_key:
    continue

  # Skip thins that dont have a sentence that matches the key
  if sentence_keys.find(input_words_key) < 0:
    continue

  # Show possible answer and increment counter
  print( title + ' => '+ sentence_keys +'"' )
  summary_count = summary_count +1 

print( 'Narrowed to: '+ str(summary_count) )
print( 'Finished' )
exit()
