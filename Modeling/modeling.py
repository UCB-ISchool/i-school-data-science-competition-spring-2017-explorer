import graphlab as gl
import math
import csv
import sys

def model_fit(feats_file,target, exclude_list):
	feats_df=gl.SFrame.read_csv(feats_file)
	print 'Target Distribution'
	print feats_df[target].sketch_summary()
	exclude_list=list(set(exclude_list))
	for each in feats_df.column_names():
		#if 'A-' in each or 'B-' in each or each=='ratio_num_children':
		if  each=='ratio_num_children':
			exclude_list.append(each)
	for each in feats_df.column_names():
		if each not in exclude_list and 'occupation' not in each.lower():
			print each
			feats_df=feats_df.fillna(each,0)
			feats_df[each]=feats_df[each].apply(lambda x:0 if math.isnan(x) or x==float('inf') else x)
	train_data, test_data_adoption = feats_df.random_split(0.66)
	features = [each for each in feats_df.column_names() if target!=each and each not in exclude_list]
	print 'Features Count', len(features)

	model = gl.boosted_trees_classifier.create(train_data, target=target,
		features=features, max_iterations=3, max_depth = 5)

	predictions = model.classify(test_data_adoption)

	results = model.evaluate(test_data_adoption)

	feats_imp=model.get_feature_importance()

	return model, predictions, results, feats_imp

if __name__=='__main__':
	feats_file=sys.argv[1]
	target='Divorced'
	exclude_list=['A','B']
	model, predictions, results, feats_imp=model_fit(feats_file, target, exclude_list)
	print 'Results\n', results
	print 'Top feats'
	print feats_imp.head()
	feats_imp.export_csv('Features_Importance.csv')	
