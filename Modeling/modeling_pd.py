import numpy as np
import pandas as pd
import math
import csv
import sys
from sklearn.ensemble import GradientBoostingClassifier
from sklearn import cross_validation, metrics
def _modelfit(alg, dtrain,dtest, predictors, performCV=True, printFeatureImportance=True, cv_folds=5, target='present'):
	#Fit the algorithm on the data
	alg.fit(dtrain[predictors], dtrain[target])
	#Predict training set:
	dtrain_predictions = alg.predict(dtrain[predictors])
	dtrain_predprob = alg.predict_proba(dtrain[predictors])[:,1]
	#Perform cross-validation:
	if performCV:
		cv_score = cross_validation.cross_val_score(alg, dtrain[predictors], dtrain[target], cv=cv_folds, scoring='roc_auc')
	#Print model report:
	print "\nModel Report"
	print "Accuracy Train: %.4g" % metrics.accuracy_score(dtrain[target].values, dtrain_predictions)
	print "AUC Score (Train): %f" % metrics.roc_auc_score(dtrain[target], dtrain_predprob)   
	if performCV:
		print "CV Score : Mean - %.7g | Std - %.7g | Min - %.7g | Max - %.7g" % (np.mean(cv_score),np.std(cv_score),np.min(cv_score),np.max(cv_score))    
	dtest_predictions=alg.predict(dtest[predictors])
	dtest_predprob = alg.predict_proba(dtest[predictors])[:,1]
	results_test= metrics.accuracy_score(dtest[target].values, dtest_predictions)
	print "Accuracy Test: %.4g" % metrics.accuracy_score(dtest[target].values, dtest_predictions)
	auc_test= metrics.roc_auc_score(dtest[target], dtest_predprob)   
	print "AUC Score (Test): %f" % metrics.roc_auc_score(dtest[target], dtest_predprob)   
	feat_imp = pd.Series(alg.feature_importances_, predictors).sort_values(ascending=False)
	return feat_imp,alg,results_test, auc_test

def model_fit(feats_file,feats_df, train_data, test_data,target, exclude_list, feat_cats, filter1):
	if filter1=='All':
		print 'Target Distribution'
		print feats_df[target].value_counts()
	exclude_list=list(set(exclude_list))
	for each in feats_df.columns:
		#if 'A-' in each or 'B-' in each or each=='ratio_num_children':
		if  'num_children' in each:
			exclude_list.append(each)
		if filter1!='All' and each not in exclude_list and each!=target and  feat_cats[each]!=filter1:
			exclude_list.append(each)	
	features = [each for each in feats_df.columns if target!=each and each not in exclude_list]
	print 'Features Count', len(features)

	gbm0=GradientBoostingClassifier(random_state=999, max_depth=10, learning_rate=0.01)
	feats, alg, acc_test, auc_test=_modelfit(gbm0, train_data,test_data,features, target=target)

	predictions = alg.predict(test_data[features])


	return alg, predictions, feats, acc_test, auc_test

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
	missing_cols=set(['occupation-actor','occupation-business','occupation-fashion','occupation-journalist',
'occupation-media','occupation-model','occupation-royality','occupation-singer','occupation-sportsman','occupation-writer','occupation-actor','occupation-cartoonist','occupation-director','occupation-engineer','occupation-fashion','occupation-journalist','occupation-media','occupation-model','occupation-musician','occupation-presenter','occupation-producer','occupation-royality','occupation-singer','occupation-sportsman'])	
	for each in missing_cols:
		feat_cats['a-'+each]='Life'
		feat_cats['b-'+each]='Life'

	categories=['All']+list(set([v for k,v in feat_cats.items()]))
	
	target='divorced'
	exclude_list=['a','b','A','B']
	feats_df=pd.read_csv(feats_file, verbose=False, index_col=0)
	
	rc=[]
	for each in feats_df.columns:
		rc.append(each.lower().strip().replace(' ','_'))
	
	feats_df.columns=rc
	for each in feats_df.columns:
		if each not in feat_cats:
			print 'Missing', each
	for each in feats_df.columns:
		if each not in exclude_list and 'occupation' not in each.lower():
			#print each
			feats_df[each]=feats_df[each].fillna(0)
			feats_df[each]=feats_df[each].apply(lambda x:0 if math.isnan(x) or x==float('inf') else x)
	np.random.seed(999)
	mask=np.random.rand(len(feats_df))<0.60
	train_data, test_data = feats_df[mask], feats_df[~mask]
	acc_dc,auc_dc={},{}
	for each in categories:
		print '*'*10, each, '*'*10
		model, predictions, feats_imp, acc_test, auc_test=model_fit(feats_file,feats_df, train_data, test_data, target, exclude_list, feat_cats=feat_cats, filter1=each)
		#print 'Results\n', results
		acc_dc[each]=acc_test
		auc_dc[each]=auc_test
		#iexport_results(results,'results_{}.csv'.format(each))
		#print 'Top feats'
		#print feats_imp.head()
		pd.DataFrame(feats_imp).to_csv('Features_Importance_{}.csv'.format(each))	

	print 'Accuracy', acc_dc
	print 'AUC', auc_dc
