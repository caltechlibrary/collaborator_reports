import os,subprocess,json,csv,string
from datetime import date,timedelta
import requests
import sys
import dataset
import urllib
from clint.textui import progress

class Coauthor:
    def __init__(self,ca_id,name,affiliation,year,link):
        self.ca_id = ca_id
        self.names = [name]
        if type(affiliation) != list:
            print(affiliations,link," Odd affiliation")
            exit()
        self.affiliations = affiliation
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
            if a != ' ':
                if alist == '':
                    alist = a
                else:
                    split = [x.strip() for x in alist.split(';')]
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

#Get input
#Enter the collection (e.g. Adhikari.ds):
#Enter the input google sheet ID:
#Enter the output google sheet ID
name = sys.argv[1]
sheet = sys.argv[2]
output_sheet = sys.argv[3]

os.system("rm -rf imported.ds")
os.system("dataset init imported.ds")

os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"
os.system("dataset import-gsheet "+sheet+" 'Sheet1' 'A:CZ' 1 -c imported.ds ")

keys = subprocess.check_output(["dataset","keys","imported.ds"],universal_newlines=True).splitlines()


#Remove group listings by simple matching
remove_words =\
    set(['collaboration','team','telescope','collaborations','network'])
remove_punctuation = str.maketrans('','',string.punctuation)

coauthors = []

count = 0
for key in keys:
    entry = json.loads(\
            subprocess.check_output(["dataset","-c","imported.ds","read",key],universal_newlines=True))
    record = json.loads(\
            subprocess.check_output(["dataset","-c",name,"read",entry['link']],universal_newlines=True))
    count = 0
    identifiers = record['identifiers']
    affiliations = record['affiliations']
    authors = record['authors'].split(';')
    link = record['link']
    year = record['year']
    for a in authors:
        author_words =set(a.translate(remove_punctuation).lower().split())
        #If none of the words in remove_words appears, we have an author
        if remove_words.intersection(author_words) == set():
            coauthors.append(Coauthor(identifiers[count],a,affiliations[count],year,link))
        count = count + 1 

print("Total authors:", len(coauthors))

#Dedupe
deduped = []
for cnt in range(len(coauthors)):
    print(cnt)
    subject = coauthors.pop()
    dupe = False
    for d in deduped:
        if d.ca_id == subject.ca_id:
            dupe = d
        if subject.names[0] in d.names and subject.affiliations[0] in d.affiliations:
            dupe = d
        if subject.names[0] in d.names and \
            (subject.affiliations[0] == ' ' or d.affiliations[0] == ' '):
            dupe = d
        if subject.family == d.family and subject.first_part == d.first_part\
        and subject.affiliations[0] in d.affiliations:
            dupe = d
        if subject.family == d.family and subject.first_part == d.first_part\
        and (subject.affiliations[0] == ' ' or d.affiliations[0] == ' '):
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
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
export_list = ".ca_id,.names,.years,.affiliations,.links"
title_list = "id,name,years,affiliations"
subprocess.run(['dataset','-c','collaborators.ds','export-gsheet',\
                    output_sheet,sheet_name,sheet_range,'true',export_list,title_list])

