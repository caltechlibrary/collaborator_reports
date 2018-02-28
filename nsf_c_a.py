import os,subprocess,json,csv,collections
from datetime import date,timedelta
import requests
import ads
import dataset
from clint.textui import progress

class Coauthor:
    def __init__(self,ca_id,name,affiliation,year,link):
        self.ca_id = ca_id
        self.names = [name]
        self.affiliations = [affiliation]
        self.years = [year]
        self.links = [link]
    def write(self):
        alist = ''
        for a in self.affiliations:
            if a != ' ':
                if alist == '':
                    alist = a
                else:
                    split = alist.split(';')
                    if a not in split:
                        alist = alist +'; '+a
        #Want the latest year
        year = 0
        for y in self.years:
            if y > year:
                year = y
        nlist = ''
        for n in self.names:
            if nlist == '':
                nlist = n
            else:
                split = nlist.split(';')
                if n not in split:
                    nlist = nlist +'; '+n
        llist = ''
        for l in self.links:
            if llist == '':
                llist = l
            else:
                llist = llist +'; '+str(l)
        json = {'ca_id':self.ca_id,\
                'names':nlist,\
                'affiliations':alist,\
                'years':year,\
                'links':llist}
        return json

#os.environ['AWS_SDK_LOAD_CONFIG']="1"

#path = "s3://dataset.library.caltech.edu/CaltechAUTHORS"
path="CaltechAUTHORS"
#path="sample"

#print("Updating data from CaltechAUTHORS")
#Should drop in a s3 sync command
#subprocess.run(['dsindexer','-c',path,'-update','authors.json','authors.bleve'])

#Get input
name = input("Enter a CaltechAUTHORS author id (e.g. Readhead-A-C-S):")

response =\
        subprocess.check_output(['dsfind','-json','-size','10000','authors.bleve','authors:'+name],universal_newlines=True)
response = json.loads(response)
keys = []
for h in response['hits']:
    keys.append(h['id'])

coauthors = []

count = 0
for k in keys:
    #print(k)
    count = count + 1
    #if count % 100 == 0:
    #    print(count)
    metadata = subprocess.check_output(["dataset","-c",path,"read",str(k)],universal_newlines=True)
    metadata = json.loads(metadata)
    #Pull out date
    if 'date' in metadata:
        split = metadata['date'].split('-')
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
        #Try to find affiliations
        affiliation = []
        if 'related_url' in metadata:
            for r in metadata['related_url']:
                if r['type'] == 'doi':
                    if r['description'] == 'Article':
                        split = r['url'].split('/')
                        doi = ''
                        for s in range(len(split)):
                            if s == 3:
                                doi = split[s]
                            if s > 3:
                                doi = doi + '/'+split[s]
                        doi = doi.strip() #trim leading/trailing spaces
                        #Crossref lookup
                        url = 'https://api.crossref.org/works/'
                        tag = ''
                        response = requests.get(url+doi+tag)
                        #ADS lookup - save records to Dataset to avoid rate limit
                        collection = "ads"
                        if os.path.exists(collection) == False:
                            dataset.init_collection(collection)
                        #print("dataset -c "+collection+" haskey "+doi)
                        #print(dataset.has_key(collection,doi))
                        if dataset.has_key(collection,doi):
                            paper = dataset.read_record(collection,doi)
                        else:
                            print(doi)
                            print("Downloading from ADS")
                            papers = ads.SearchQuery(doi=doi,fl=['aff','author'])
                            c = 0
                            for p in papers:
                                if c > 0:
                                    print("Multiple papers found from ADS for"+doi)
                                else:
                                    paper = {'aff':p.aff,'author':p.author}
                                    ok = dataset.create_record(collection,doi,paper)
                                c = c + 1
                        ads_affiliations = paper['aff']
                        ads_authors = paper['author']
                        #We're going to go through all authors listed in CaltechAUTHORS
                        for anum in range(len(metadata['creators'])):
                            a = metadata['creators'][anum]
                            for author in response.json()['message']['author']:
                                if 'family' in author:
                                    if author['family'] == a['family']:
                                        if author['given'] == a['given']:
                                            if author['affiliation'] != []:
                                                affiliation.append(author['affiliation'].strip())
                                            #elif 'ORCID' in author:
                                            #    affiliation.append(author['ORCID'])
                            if len(affiliation) != anum+1:
                                #Check ADS Data
                                index = 0
                                for author in ads_authors:
                                    family = author.split(',')[0].strip()
                                    if family == a['family']:
                                        affiliation.append(ads_affiliations[index].strip())
                                    index = index + 1
                            if len(affiliation) != anum+1:
                                affiliation.append(' ')

        link = metadata['official_url']
        authors = metadata['creators']
        for anum in range(len(authors)):
            a = authors[anum]
            if len(affiliation) != 0:
                affil = affiliation[anum]
            else:
                affil = ''
            if a['id'] != name:
                coauthors.append(Coauthor(a['id'],a['family']+','+a['given'],affil,publication_date.year,link))
        print(len(coauthors))

#Dedupe
deduped = []
for cnt in range(len(coauthors)):
    subject = coauthors.pop()
    dupe = False
    for d in deduped:
        if d.ca_id == subject.ca_id:
            dupe = True
            if subject.affiliations not in d.affiliations:
                d.affiliations = d.affiliations + subject.affiliations
            if subject.years not in d.years:
                d.years = d.years + subject.years
            if subject.names not in d.names:
                d.names = d.names + subject.names
            if subject.links not in d.links:
                d.links = d.links + subject.links
    if dupe == False:
        deduped.append(subject)

print(len(deduped))
subprocess.run(['rm','-rf','collaborators'])
subprocess.run(['dataset','init','collaborators'])
for d in deduped:
    subprocess.run(['dataset','-quiet','-nl','false','-i','-','-c','collaborators','create',d.ca_id],\
                            input=json.dumps(d.write()),universal_newlines=True)
#Export to Google Sheet
os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"

#Google sheet ID for output
output_sheet = "1_p054rcvNzPM3MfvCJJP_zWXVxACWwHqI82qTsd1CoQ"
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
export_list = ".ca_id,.names,.years,.affiliations,.links"
title_list = "id,name,years,affiliations"
subprocess.run(['dataset','-c','collaborators','export-gsheet',\
                    output_sheet,sheet_name,sheet_range,'true',export_list,title_list])

