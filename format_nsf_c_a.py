import os,subprocess,json,csv,string
from datetime import date,timedelta
import requests
import sys
from py_dataset import dataset
import urllib
import argparse
from progressbar import progressbar

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

def remove_punctuation(input_string):
    punctuation = str.maketrans('','',string.punctuation)
    return input_string.translate(punctuation)

def contains_exclusion_word(input_string):
    #Remove group listings by simple matching
    remove_words =\
            set(['collaboration','team','telescope','collaborations','network'])
    author_words =set(remove_punctuation(a).lower().split())
    #If none of the words in remove_words appears, we have an author
    if remove_words.intersection(author_words) == set():
        return False
    else:
        return True

def same_affiliation(first,second):
    first_set = set(remove_punctuation(first).lower().split())
    second_set = set(remove_punctuation(second).lower().split())
    overlap = len(first_set.intersection(second_set))
    if overlap > 4:
        return True
    else:
        return False

def match_affiliations(first,second):
    match = False
    for f in first:
        for s in second:
            if same_affiliation(f,s):
                match = True
            #Always match to blanks
            if f == ' '  or s == ' ':
                mach = True
    return match

def combine_affiliations(first,second):
    #We make start with a random guess that the second list is correct
    comb_affil = second.copy()
    for f in first:
        saved = False
        for s in comb_affil:
            if same_affiliation(f,s):
                saved = True
                #We use size to judge which to keep
                if len(f) > len(s):
                    comb_affil.remove(s)
                    comb_affil.append(f)
        if saved == False:
            comb_affil.append(f)
    if len(comb_affil) > 1:
        if ' ' in comb_affil:
            comb_affil.remove(' ')
    return comb_affil

#Get input
#Enter the collection (e.g. Adhikari.ds):
#Enter the input google sheet ID:
#Enter the output google sheet ID

parser = argparse.ArgumentParser(description=\
        "Generate a formatted Collaborator Report for the NSF Part C Section A")
parser.add_argument('data_collection', nargs=1, help=\
            'file name for the dataset collection with harvested data')
parser.add_argument('input_sheet', nargs=1, help=\
        'Input Google Sheet ID with author citations')
parser.add_argument('output_sheet', nargs=1, help='Output Google Sheet ID')
parser.add_argument('-limited', action='store_true', help=\
        'Save only the first three authors')
args = parser.parse_args()

name = args.data_collection[0]
sheet = args.input_sheet[0]
output_sheet = args.output_sheet[0]

import_coll = "imported.ds"
os.system("rm -rf imported.ds")
dataset.init(import_coll)

os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"
err = dataset.import_gsheet(import_coll,sheet,'Sheet1',1,'A:CZ')
if err != '':
    print(err)

keys = dataset.keys(import_coll)

coauthors = []

count = 0
for key in progressbar(keys, redirect_stdout=True):
    record,err = dataset.read(name,key)
    if err != "":
        print(err)
    count = 0
    if 'identifiers' in record:
        identifiers = record['identifiers']
    else:
        identifiers = []
    print(key)
    print(record)
    affiliations = record['affiliations']
    authors = record['authors'].split(';')
    link = record['link']
    year = record['year']
    for a in authors:
        #If none of the words in remove_words appears, we have an author
        if contains_exclusion_word(a) == False:
            coauthors.append(Coauthor(identifiers[count],a,affiliations[count],year,link))
        if args.limited == True:
            if count>=2:
                print("Dropping authors due to limited option")
                break
        count = count + 1 

print("Total authors: ", len(coauthors))

#Dedupe
deduped = []
for cnt in progressbar(range(len(coauthors)), redirect_stdout=True):
    subject = coauthors.pop()
    dupe = False
    for d in deduped:
        if d.ca_id == subject.ca_id:
            dupe = d
        if subject.names[0] in d.names and match_affiliations(subject.affiliations,d.affiliations):
            dupe = d
        if subject.family == d.family and subject.first_part == d.first_part\
        and match_affiliations(subject.affiliations,d.affiliations):
            dupe = d

    if dupe == False:
        #This is a new author
        deduped.append(subject)
    else:
        #Save any unique metadata
        dupe.affiliations = combine_affiliations(subject.affiliations,dupe.affiliations)
        if subject.years not in dupe.years:
            dupe.years += subject.years
        if subject.names not in dupe.names:
            dupe.names += subject.names
        if subject.links not in dupe.links:
            dupe.links += subject.links

print("Total collaborators: ",len(deduped))

collab = 'collaborators.ds'

subprocess.run(['rm','-rf',collab])
dataset.init(collab)
for d in deduped:
    dataset.create(collab,d.ca_id,d.write())
#Export to Google Sheet
os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"

#Google sheet ID for output
f_name = 'frm'
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
export_list = [".names",".years",".affiliations",".links"]
title_list = ["name","years","affiliations","links"]
keys = dataset.keys(collab)
if dataset.has_frame(collab, f_name):
    dataset.delete_frame(collab, f_name)
frame, err = dataset.frame(collab,f_name,keys,export_list,title_list)
if err != '':
    print(err)
err = dataset.export_gsheet(collab,f_name,output_sheet,sheet_name,sheet_range)
if err != '':
    print(err)
