import os,subprocess,json,csv,collections
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
        self.affiliations = [affiliation]
        self.years = [year]
        self.links = [link]
    def write(self):
        alist = ''
        print(self.affiliations)
        for a in self.affiliations:
            if a != ' ':
                if alist == '':
                    alist = a
                else:
                    split = alist.split(';')
                    if a not in split:
                        alist = alist +'; '+a
        #Want the latest year
        print('year')
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
list(ads.SearchQuery(author=name,fl=['aff','author','pubdate','doi','orcid'],rows=5000,max_pages=100))

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
    #We're going to do further processing
    if keep == True:
        for a in range(len(record.author)):
            if record.orcid == None:
                if record.doi == None:
                    coauthors.append(Coauthor(record.author[a],record.author[a],record.aff[a],pubdate.year,''))
                else:
                    coauthors.append(Coauthor(record.author[a],record.author[a],record.aff[a],pubdate.year,record.doi[0]))
            else:
                coauthors.append(Coauthor(record.orcid[a],record.author[a],record.aff[a],pubdate.year,record.doi[0]))

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
subprocess.run(['rm','-rf','collaborators.ds'])
subprocess.run(['dataset','init','collaborators.ds'])
for d in deduped:
    subprocess.run(['dataset','-i','-','-c','collaborators.ds','create',d.ca_id],\
                            input=json.dumps(d.write()),universal_newlines=True)
#Export to Google Sheet
os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"

#Google sheet ID for output
output_sheet = "1VSJwLHq5r_S98d0_V-PchlOEofrE0U2DHCSzGFAQhlA"
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
export_list = ".ca_id,.names,.years,.affiliations,.links"
title_list = "id,name,years,affiliations"
subprocess.run(['dataset','-c','collaborators.ds','export-gsheet',\
                    output_sheet,sheet_name,sheet_range,'true',export_list,title_list])

