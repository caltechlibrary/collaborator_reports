import os,subprocess,json,csv,collections
from datetime import date,timedelta
import requests
import ads
import dataset
from clint.textui import progress

path="CaltechAUTHORS.ds"

#subprocess.run(['dataset',path,'indexer','authors.json','authors.bleve'])

#authors = ['Anderson-D-J','Aravin-A-A','Arnold-F-H']

authors = []
infile = open('authors.txt','r')
for line in infile:
    authors.append(line.strip())

#Eprints records with co-authored papers
records = []

for a in authors:
    print(a)
    response =\
        subprocess.check_output(['dataset','-json','-size','10000','find','authors.bleve','authors:'+a],universal_newlines=True)
    response = json.loads(response)
    keys = []
    for h in response['hits']:
        keys.append(h['id'])
    count = 0
    for k in keys:
        #print(k)
        metadata = subprocess.check_output(["dataset","-c",path,"read",str(k)],universal_newlines=True)
        metadata = json.loads(metadata)
        #Pull out date
        if 'date' in metadata:
            split = metadata['date'].split('-')
            try:
                if len(split) == 3:
                    publication_date = date(int(split[0]),int(split[1]),int(split[2]))
                elif len(split) == 2:
                    publication_date = date(int(split[0]),int(split[1]),1)
                elif len(split) == 1:
                    publication_date = date(int(split[0]),1,1)
                else:
                    print("Record "+str(k)+"has a weird date - skipping")
                    publication_data = date(1,1,1)
            except ValueError:
                print("Record "+str(k)+"has a weird date - skipping")
                publication_date = date(1,1,1)
            today = date.today()
            time_lag = timedelta(days=532900) #We care about records in the past ten years
            cutoff = today - time_lag
            if publication_date > cutoff:
                author_ids = []
                for c in metadata['creators']:
                    author_ids.append(c['id'])
                #print('COMP',authors,author_ids)
                #print(set(authors).intersection(author_ids))
                match = set(authors).intersection(author_ids)
                if len(match) > 1:
                    print('Yes!')
                    records.append(metadata)
        else:
            print("Record "+str(k)+"does not have date, discarding")

ids = []
for r in records:
    idv = r['id']
    if idv not in ids:
        ids.append(idv)
        citation = ''
        for c in r['creators']:
            citation = citation + c['family'] +', '+ c['given'] +'; '
        citation = citation + ' (' + r['date'].split('-')[0] + ') '
        citation = citation + r['title'] + '.'
        if 'publication' in r:
            citation = citation + ' ' + r['publication']
        citation = citation + ' ' + r['official_url']
        print(citation)
