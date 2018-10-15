import os,subprocess,json,csv,string
from datetime import date,timedelta
import requests
import ads
import dataset
import urllib
from clint.textui import progress

class Coauthor:
    def __init__(self,ca_id,name,affiliation,year,link):
        self.ca_id = ca_id
        self.names = [name]
        split = affiliation.split(';')
        self.affiliations = []
        for a in split:
            self.affiliations.append(a.strip())
        self.years = [year]
        self.links = [link]
        split = name.split(' ')
        self.family = split[0].split(',')[0]
        if len(split) > 1:
            self.first_part = split[1]
        else:
            self.first_part = ''
    def write(self):
        alist = ''
        for a in self.affiliations:
            if alist == '':
                alist = a 
            else:
                alist = alist + ';' + a
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

#Make sure to set ADS key as ADS_DEV_KEY environement variable
#https://ads.readthedocs.io/en/latest/

#Get input
name = input("Enter a ADS author search term (e.g. Mooley, K):")

records =\
list(ads.SearchQuery(author=name,fl=['aff','author','pubdate','doi',
    'orcid_pub','orcid_user','orcid_other','bibcode'],rows=5000,max_pages=100))

coauthors = []

count = 0
print("Records: ",len(records))
for record in records:
    #print(k)
    count = count + 1
    #if count % 100 == 0:
    #    print(count)
    #Pull out date
    today = date.today()
    time_lag = timedelta(days=1460) #We care about records in the past four years
    cutoff = today - time_lag
    raw_date = record.pubdate.split('-')
    year = int(raw_date[0])
    month = int(raw_date[1])
    day = int(raw_date[2])
    if month == 0:
        month = 1
    if day == 0:
        day = 1
    pubdate = date(year,month,day)
    keep = pubdate > cutoff
    #Remove group listings by simple matching
    remove_words =\
    set(['collaboration','team','telescope','collaborations','network'])
    remove_punctuation = str.maketrans('','',string.punctuation)
    #We're going to do further processing
    if keep == True:
        for a in range(len(record.author)):
            idv = '-'
            if record.orcid_pub != None:
                idv = record.orcid_pub[a]
            if record.orcid_user != None:
                if idv == '-':
                    idv = record.orcid_user[a]
            if record.orcid_other != None:
                if idv == '-':
                    idv = record.orcid_other[a]
            if idv == '-':
                idv = 'D'+str(len(coauthors))
            if record.doi == None:
                url = record.bibcode
            else:
                url = record.doi[0]
            author_words =\
            set(record.author[a].translate(remove_punctuation).lower().split())
            #If none of the words in remove_words appears, we have an author
            if remove_words.intersection(author_words) == set():
                #Remove strict author match; should be updated with author searching
                if record.author[a] != name:
                    coauthors.append(Coauthor(idv,record.author[a],record.aff[a],pubdate.year,url))
            
        print(len(coauthors))

#Dedupe
deduped = []
for cnt in range(len(coauthors)):
    subject = coauthors.pop()
    dupe = False
    for d in deduped:
        if d.ca_id == subject.ca_id:
            dupe = d
        if subject.names[0] in d.names and subject.affiliations[0] in d.affiliations:
            dupe = d
        if subject.names[0] in d.names and \
            (subject.affiliations[0] == '-' or d.affiliations[0] == '-'):
            dupe = d
        if subject.family == d.family and subject.first_part == d.first_part\
        and subject.affiliations[0] in d.affiliations:
            dupe = d
        if subject.family == d.family and subject.first_part == d.first_part\
        and (subject.affiliations[0] == '-' or d.affiliations[0] == '-'):
            dupe = d

    if dupe == False:
        #This is a new author
        deduped.append(subject)
    else:
        #Save any unique metadata
        if subject.affiliations not in dupe.affiliations:
            if subject.affiliations != '-':
                dupe.affiliations += subject.affiliations
        if subject.years not in dupe.years:
            dupe.years += subject.years
        if subject.names not in dupe.names:
            dupe.names += subject.names
        if subject.links not in dupe.links:
            dupe.links += subject.links

print(len(deduped))
subprocess.run(['rm','-rf','collaborators.ds'])
subprocess.run(['dataset','init','collaborators.ds'])
for d in deduped:
    subprocess.run(['dataset','-i','-','-c','collaborators.ds','create',d.ca_id],\
                            input=json.dumps(d.write()),universal_newlines=True)
#Export to Google Sheet
os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"

#Google sheet ID for output
output_sheet = "1rXamt4R7nGxPLS5awRMpbpWidGYBx4bQRVViSXdwlco"
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
export_list = ".ca_id,.names,.years,.affiliations,.links"
title_list = "id,name,years,affiliations"
subprocess.run(['dataset','-c','collaborators.ds','export-gsheet',\
                    output_sheet,sheet_name,sheet_range,'true',export_list,title_list])

