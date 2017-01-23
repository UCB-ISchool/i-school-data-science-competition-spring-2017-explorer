
import os
import os.path
import re
import requests
import unicodedata
import pandas as pd
from wikiapi import WikiApi# library to get complete wiki content


def checkForConfigFile():
    filename='user-config.py'
    if not os.path.isfile(filename):
        lst=["mylang = \'en\'",
             "family = \'wikinews\'",
             "usernames[\'wikinews\'][\'en\'] = u\'mraza.uw\'"]
        with open(filename,'w') as fout:
            for each in lst:
                fout.write(each+'\n')



wiki = WikiApi()

import mwparserfromhell # parser to parse wiki infoboxes
checkForConfigFile() #make sure that the config file for the pywikibot is there
import pywikibot # for infoboxes


'''Read Celebrities name from the file containing marital status of the celebrities'''

def getCelebrityList(filename='raw.csv'):
    celebs=[]
    with open(filename) as fin:
        fin.next()
        for each in fin:
            lst=each.split(',')
            celebs.append(lst[0].strip())
            celebs.append(lst[1].strip())
    return celebs





'''get the content of the wiki infobox'''
def extract_infobox(celeb_name):
    enwp = pywikibot.Site('en','wikipedia')
    page = pywikibot.Page(enwp, celeb_name)
    wikitext = page.get()
    wikicode = mwparserfromhell.parse(wikitext)
    templates = wikicode.filter_templates()
    dc={}
    infobox=None
    for each in templates:
            if 'Infobox' in each:
                    infobox=each
                    break
    if infobox:
            for param in infobox.params:
                    dc[param.name.encode('ascii','ignore').strip()]=param.value.encode('ascii','ignore').strip()
                    
            if 'children' in dc:
                num=re.findall(r'\d',dc['children'])
                if num:
                    dc['num_children']=num[0]
                else:
                    #remove every thing before father or mother
                    children=dc['children'].split('father')[0].split('mother')[0]
                    children=''.join(e for e in children if e.isalnum())
                    dc['num_children']=len(filter(None,children.split('br')))
            
            if 'partner' in dc:
                temp=dc['partner']
                dc['partners_list']=filter(None,re.findall(r'\[\[(.*?)\]\]', temp)  )
                        
    return dc



'''get the content of the wiki'''
def get_wiki_content(celeb_name):
    content=wiki.get_article(celeb_name).content
    return content

''' export wiki content'''
def export_wiki_content(celebs_list, outfilename='celebs_wiki_content.csv'):
	celebs_page_content={}
	parents_reference={}
	missing_content=[]
	for celeb in celebs_list:
	    try:
		celebs_page_content[celeb]=get_wiki_content(celeb).encode('ascii','ignore').replace(';',' ')
		txt=celebs_page_content[celeb]
		for each in txt.split('\n'):
			if 'parent' in each or 'father' in each or 'mother' in each:
				if celeb in parents_reference:
					parents_reference[celeb].append(each)
				else:
					parents_reference[celeb]=[each]
		celebs_page_content[celeb]=celebs_page_content[celeb].replace('\n',' ')
	    except:
		missing_content.append(celeb)
		pass
	    
	# Exporting the wiki content to csv
	with open(outfilename, 'w') as f:
	    [f.write('{0};{1}\n'.format(key, value)) for key, value in celebs_page_content.items()]
	
	with open('parents_reference.csv', 'w') as f:
	    [f.write('{0};{1}\n'.format(key, ' '.join(each for each in value))) for key, value in parents_reference.items()]
	
	return celebs_page_content, missing_content, parents_reference

def export_parents_divorce_stats(celebs_list, celebs_page_content, outfilename='parents_divorce_stats.csv'):
	parents_divorce={}
	for celeb in celebs_list:
	    if 'parents divorce' in celebs_page_content[celeb]:
		print celeb
		parents_divorce[celeb]=1

	# Exporting the wiki content to csv
	with open(outfilename, 'w') as f:
	    [f.write('{0};{1}\n'.format(key, value)) for key, value in parents_divorce.items()]
	return parents_divorce


def export_wiki_infobox(celebs_list, outfilename='celebs_info.csv'):
	missing_list=[]
	celebs_info={}
	for celeb in celebs_list:
	    try:
		celebs_info[celeb]=extract_infobox(celeb)
	    except:
		missing_list.append(celeb)
		pass
	missing={}
	for i,k in enumerate(celebs_info.keys()):
	    celeb_name=celebs_info.keys()[i]
	    dc=celebs_info[celeb_name]
	    partners=[]
	    if 'partner' in dc:
		temp=dc['partner']
		partners=filter(None,re.findall(r'\[\[(.*?)\]\]', temp)  )    
	    elif 'spouse' in dc:
		temp=dc['spouse']
		partners=filter(None,re.findall(r'\[\[(.*?)\]\]', temp)  )    
		try:    
		    if len(partners)==0:
			if ('{') in dc['spouse']:
			    partners=filter(None,re.findall(r'\{\{(.*?)\}\}', temp)  )    
			partners=re.findall(r'marriage\|.*?\|', temp['spouse'])
			print celeb_name, partners
			partners=[each.split('|')[1] for each in partners]
			print celeb_name, partners
		except:
		    pass
		celebs_info[celeb_name]['partner']=partners
	    if len(partners)==0:
		missing[celeb_name]=dc

	missing_occupation={}
	for each in celebs_info:
	    if 'occupation' not in celebs_info[each]:
		missing_occupation[each]=celebs_info[each]
	    else:
		celebs_info[each]['occupation']=celebs_info[each]['occupation'].replace('\n',' ')

	# keeping only the required elements in the infobox
	to_keep=['partner','occupation','num_children']

	celebs_info2={}	
	for each in celebs_info:
		temp={}
		for k in celebs_info[each]:
			if k  in to_keep:
				temp[k]= celebs_info[each][k]
		for j in to_keep:
			if j not in temp:
				temp[j]=''
		celebs_info2[each]=temp
	# Exporting the wiki content to csv
	with open(outfilename, 'w') as f:
	    [f.write('{0};{1}\n'.format(key, value)) for key, value in celebs_info2.items()]

	df=pd.DataFrame.from_dict(celebs_info2, orient='index')	
	df.to_csv('wiki_info_df.csv')	
	return celebs_info2

''''
if __name__=='__main__':

	celebs_list=getCelebrityList()
	celebs_page_content, missing_content=export_wiki_content(celebs_list)
	celebs_parents_divorce=export_parents_divorce_stats(celebs_list, celebs_page_content)
	celebs_info=export_wiki_infobox(celebs_list)

'''
		



