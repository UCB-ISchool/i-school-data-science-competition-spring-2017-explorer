import graphlab as gl
import math
import csv
import sys

def model_fit(feats_file,target, exclude_list, feat_cats, filter1):
	feats_df=gl.SFrame.read_csv(feats_file, verbose=False)
	rc={}
	for each in feats_df.column_names():
		rc[each]=each.lower().strip().replace(' ','_')
	feats_df=feats_df.rename(rc)
	if filter1=='All':
		print 'Target Distribution'
		print feats_df[target].sketch_summary()
	exclude_list=list(set(exclude_list))
	for each in feats_df.column_names():
		#if 'A-' in each or 'B-' in each or each=='ratio_num_children':
		if  each=='ratio_num_children':
			exclude_list.append(each)
		if filter1!='All' and each not in exclude_list and each!=target and  feat_cats[each]!=filter1:
			exclude_list.append(each)	
	for each in feats_df.column_names():
		if each not in exclude_list and 'occupation' not in each.lower():
			feats_df=feats_df.fillna(each,0)
			feats_df[each]=feats_df[each].apply(lambda x:0 if math.isnan(x) or x==float('inf') else x)
	train_data, test_data_adoption = feats_df.random_split(0.66)
	features = [each for each in feats_df.column_names() if target!=each and each not in exclude_list]
	print 'Features Count', len(features)

	model = gl.boosted_trees_classifier.create(train_data, target=target,
		features=features)

	predictions = model.classify(test_data_adoption)

	results = model.evaluate(test_data_adoption)

	feats_imp=model.get_feature_importance()

	return model, predictions, results, feats_imp

def export_results(dc, outfile):
	with open(outfile,'w') as fout:
		for k,v in dc.iteritems():
			fout.write(k+','+str(v)+'\n')

if __name__=='__main__':
	feats_file=sys.argv[1]
	feats_categories_file=sys.argv[2]
	feat_cats={}
	results_acc={}
	with open(feats_categories_file) as fin:	
		fin.next()
		for each in fin:
			k,v=each.strip().split(',')
			feat_cats[k]=v
			feat_cats['a-'+k]=v
			feat_cats['b-'+k]=v
			feat_cats['sum_'+k]=v
			feat_cats['same_'+k]=v
			feat_cats['ratio_'+k]=v
	#print feat_cats
	categories=['All']+list(set([v for k,v in feat_cats.items()]))
	
	for each in categories:
		print '*'*10, each, '*'*10
		target='divorced'
		exclude_list=['a','b']
		model, predictions, results, feats_imp=model_fit(feats_file, target, exclude_list, feat_cats=feat_cats, filter1=each)
		#print 'Results\n', results
		results_acc[each]=results['accuracy']
		export_results(results,'results_{}.csv'.format(each))
		#print 'Top feats'
		#print feats_imp.head()
		feats_imp.export_csv('Features_Importance_{}.csv'.format(each))	

	print results_acc
