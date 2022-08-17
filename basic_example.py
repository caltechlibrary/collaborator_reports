import os,subprocess,json,csv,collections
from datetime import date,timedelta
import requests
import ads
from py_dataset import dataset
import urllib

#Get access token from WOS sed as environment variable with source token.bash
token = os.environ['WOSTOK']

headers = {
        'X-ApiKey' : token,
        'Content-type': 'application/json'
    }

#Get input
name = input("Enter a WOS author search term (e.g. Mooley K):")
caltech = input("Restrict to Caltech-affiliated papers? Y or N:")

base_url = 'https://api.clarivate.com/api/wos/?databaseId=WOK'
url = base_url + '&count=100&firstRecord=1'

if caltech == 'Y':
    query = 'AU=('+name+') AND OG=(California Institute of Technology)'
else:
    query = 'AU=('+name+')'
query = urllib.parse.quote_plus(query)
url = url+'&usrQuery='+query

print(url)
response = requests.get(url,headers=headers)
print(response.headers)
response = response.json()
record_count = response['QueryResult']['RecordsFound']
print(record_count," Records from WOS")
query_id = response['QueryResult']['QueryID']
records = response['Data']['Records']['records']['REC']

print(json.dumps(records, indent=4))
exit()

#We have saved the first 100 records
record_start = 101
record_count = record_count-100

query_url = 'https://api.clarivate.com/api/wos/query/'

while record_count > 0:
    print(record_count)
    print(len(records),'records')
    if record_count > 100:
        url = query_url + str(query_id) + '?count=100&firstRecord=' +\
            str(record_start)
        response = requests.get(url,headers=headers)
        response = response.json()
        records = records + response['Records']['records']['REC']
        record_start = record_start + 100
        record_count = record_count - 100
    else:
        url = query_url + str(query_id) + '?count=' +\
        str(record_count) + '&firstRecord='+ str(record_start)
        response = requests.get(url,headers=headers)
        response = response.json()
        records = records + response['Records']['records']['REC']
        record_count = 0

print("Downloaded records ", len(records))

coauthors = []

count = 0
for r in records:
    uid = r['UID']
    metadata = r['static_data']['summary']
    #print(k)
    count = count + 1
    #if count % 100 == 0:
    #    print(count)
    #Pull out date
    if 'sortdate' in metadata['pub_info']:
        split = metadata['pub_info']['sortdate'].split('-')
        if len(split) == 3:
            publication_date = date(int(split[0]),int(split[1]),int(split[2]))
        elif len(split) == 2:
            publication_date = date(int(split[0]),int(split[1]),1)
        elif len(split) == 1:
            publication_date = date(int(split[0]),1,1)
        else:
            print("Record "+str(k)+"has a weird date - error")
            break
        today = date.today()
        time_lag = timedelta(days=1460) #We care about records in the past four years
        cutoff = today - time_lag
        keep = publication_date > cutoff
    else:
        print("Record "+str(k)+"does not have date, discarding")
        publication_date = ''
        keep = False
    #We're going to do further processing
    if keep == True:
        title = ''
        journal = ''
        for t in metadata['titles']['title']:
            if t['type'] == 'item':
                title = t['content']
            if t['type'] == 'source':
                journal = t['content']
        authors = metadata['names']['name']
        address_data = []
        if r['static_data']['fullrecord_metadata']['addresses']['count'] > 0:
            address_data =\
                r['static_data']['fullrecord_metadata']['addresses']['address_name']
        addresses = {}
        #Set up address dictionary
        if type(address_data) == list:
            for a in address_data:
                if 'address_spec' in a:
                    if type(a) == dict:
                        data = a['address_spec']
                        addresses[data['addr_no']] = data['full_address']
                    else:
                        print(r)
                        print("Bad data")
                else:
                    print(r)
                    print("Bad Address")
        else:
            #Just one address
            data = address_data['address_spec']
            addresses[data['addr_no']] = data['full_address']
        # set up author list
        author_list = ''
        affiliation_list = []
        identifier_list = []
        if type(authors) != list:
            authors = [authors]
        for a in authors:
            if author_list == '':
                author_list = a['full_name']
            else:
                author_list+=';'+a['full_name']
            affil = []
            if 'addr_no' in a:
                if type(a['addr_no']) == int:
                    if len(addresses) >= a['addr_no']:
                        address = addresses[a['addr_no']]
                        if address == []:
                            affil.append(' ')
                        else:
                            affil.append(address)
                    else:
                        affil.append(' ')
                else:
                    #There are multiple address numbers
                    addr_list = a['addr_no'].split(' ')
                    for addr in addr_list:
                        affil.append(addresses[int(addr)])
            if affil == []:
                #There is no address reference for the author
                affil = [' ']
            affiliation_list.append(affil)
            if 'wos_standard' in a:
                identifier_list.append(a['wos_standard'])
            else:
                identifier_list.append(a['full_name'])
        link = ''
        identifiers = r['dynamic_data']['cluster_related']['identifiers']['identifier']
        if type(identifiers) == list:
            for idv in identifiers:
                if idv['type'] == 'xref_doi':
                    link = 'https://doi.org/'+idv['value']
                elif idv['type'] == 'doi':
                    link = 'https://doi.org/'+idv['value']
                else:
                    #We're just going to use the the first other identifier as filler
                    if link == '':
                        link = idv['value']
        else:
            #Just one identifier
            if identifiers['type'] == 'xref_doi':
                link = 'https://doi.org/'+idv['value']
            elif identifiers['type'] == 'doi':
                link = 'https://doi.org/'+idv['value']
            else:
                link = idv['value']    

        record =\
                {'id':uid,'title':title,'journal':journal,'authors':author_list,'identifiers':identifier_list,'affiliations':affiliation_list,'link':link,'year':publication_date.year} 

        print(record)

