import os,subprocess,json,csv,string
from datetime import date,timedelta
import requests
import sys
import dataset
import urllib
import argparse
from progressbar import progressbar

collab = 'collaborators.ds'
output_sheet = '1J59-F5WWXQX3xe3TneV5UVdHpBkph9TLW4dORGjrn8Y'

title_list = ["name","years","affiliations"]

#keys = dataset.keys(collab)
#for k in progressbar(keys):
#    start,err = dataset.read(collab,k)
#    for t in title_list:
#        if len(start['affiliations']) > 50000:
#            print(len(start['affiliations']))
#            print("Found issue")
#exit()

#Export to Google Sheet
os.environ['GOOGLE_CLIENT_SECRET_JSON']="/etc/client_secret.json"

#Google sheet ID for output
f_name = 'frm'
sheet_name = "Sheet1"
sheet_range = "A1:CZ"
export_list = [".names",".years",".affiliations"]
keys = dataset.keys(collab)
if dataset.has_frame(collab, f_name):
    dataset.delete_frame(collab, f_name)
frame, err = dataset.frame(collab,f_name,keys,export_list)
if err != '':
    print(err)
err = dataset.frame_labels(collab,f_name,title_list)
if err != '':
    print(err)
err = dataset.export_gsheet(collab,f_name,output_sheet,sheet_name,sheet_range)
if err != '':
    print(err)
