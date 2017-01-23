import graphlab 
import csv
import sys
from graphlab.toolkits.feature_engineering import SentenceSplitter

def sentiments_analysis(in_file, out_file, exclude_divorce):
	print 'Reading File'
	sf=graphlab.SFrame.read_csv(in_file, header=None, delimiter=';')
	sf=sf.rename({'X1':'celeb','X2':'text'})
	if exclude_divorce =='1':
		#filter1=SentenceSplitter()
		sf['text']=sf['text'].apply(lambda x:x.split('.')).apply(lambda x:'.'.join(y for y in x))

	print 'Shape of the data', sf.shape
	model = graphlab.sentiment_analysis.create(sf, features=['text'])
	sf['sentiment']=model.predict(sf)
	sf[['celeb','sentiment']].export_csv(out_file,quote_level=csv.QUOTE_NONE)

if __name__=='__main__':
	infile, outfile, exclude_divorce=sys.argv[1], sys.argv[2], sys.argv[3]
	
	sentiments_analysis(infile, outfile, exclude_divorce)
