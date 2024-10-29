import argparse
import sqlite3
import re

#------------------------------------------------------------------------------
def parse_inputs():
  ap = argparse.ArgumentParser()
  ap.add_argument( "-d", "--data_file", required=False,  help="Data file to use", default='wiki_data.db')
  ap.add_argument( "-t", "--title",     required=True,   help="Title copied from Redactle")
  ap.add_argument( "-w", "--words",     required=False,  help="Words copied from Redactle", default="")
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

print( 'Title Key = "'+ input_title +'"')
input_title_key = make_data_key( input_title.replace('█','x') )
input_words_key = make_data_key( input_words.replace('█','x') )

print( 'Title Key:'+ input_title_key )
print( 'Words Key:'+ input_words_key )

# Find matching records from the database file
db_con = sqlite3.connect(data_file)
db_cur = db_con.cursor()
sql    = "SELECT title FROM articles where title_key=? and word_keys like ? order by title"
parms  = ( input_title_key, '%'+ input_words_key +'%' )
data_to_check = db_cur.execute( sql, parms ).fetchall()

for record in data_to_check:
  print( ' -> '+ record[0] )
print( 'Narrowed to: '+ str(len(data_to_check)) )

print( 'Finished' )
exit()
