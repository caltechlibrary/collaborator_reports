import os, shutil, json, subprocess
from datetime import datetime
import requests, urllib
from py_dataset import dataset


def write_records(records, collection):
    for r in records:
        key = r["UID"]
        print(key)
        err = dataset.create(collection, key, r)
        if err != "":
            print(f"Unexpected error on create: {err}")


def get_wos_refs(new=True):
    # New=True will download everything from scratch and delete any existing records

    collection = "wos_refs.ds"

    if new == True:
        if os.path.exists(collection) == True:
            shutil.rmtree(collection)

    if os.path.isdir(collection) == False:
        ok = dataset.init(collection)
        if ok == False:
            print("Dataset failed to init collection")
            exit()

    # Get access token from WOS sed as environment variable with source token.bash
    token = os.environ["WOSTOK"]

    headers = {"X-ApiKey": token, "Content-type": "application/json"}

    # Run query to get scope of records

    base_url = "https://api.clarivate.com/api/wos/?databaseId=WOK"

    collected = dataset.has_key(collection, "captured")

    if collected == True:
        date = dataset.read(collection, "captured")
        date = date[0]["captured"]
        date = datetime.fromisoformat(date)
        current = datetime.today()
        diff = current - date
        base_url = base_url + "&loadTimeSpan=" + str(diff.days) + "D"

    date = datetime.today().isoformat()
    record = {"captured": date}
    if dataset.has_key(collection, "captured"):
        err = dataset.update(collection, "captured", record)
        if err != "":
            print(f"Unexpected error on update: {err}")
    else:
        err = dataset.create(collection, "captured", record)
        if err != "":
            print(f"Unexpected error on create: {err}")

    query = "OG=(California Institute of Technology) AND PY=(2015-2019)"
    query = urllib.parse.quote_plus(query)
    url = base_url + "&usrQuery=" + query + "&count=100&firstRecord=1"

    response = requests.get(url, headers=headers)
    response = response.json()
    record_count = response["QueryResult"]["RecordsFound"]
    print(record_count, " Records from WOS")
    query_id = response["QueryResult"]["QueryID"]
    records = response["Data"]["Records"]["records"]["REC"]
    write_records(records, collection)
    # We have saved the first 100 records
    record_start = 101
    record_count = record_count - 100

    query_url = "https://api.clarivate.com/api/wos/query/"

    while record_count > 0:
        print(record_count)
        print(len(records), "records")
        if record_count > 100:
            url = (
                query_url
                + str(query_id)
                + "?count=100&firstRecord="
                + str(record_start)
            )
            response = requests.get(url, headers=headers)
            response = response.json()
            records = response["Records"]["records"]["REC"]
            write_records(records, collection)
            record_start = record_start + 100
            record_count = record_count - 100
        else:
            url = (
                query_url
                + str(query_id)
                + "?count="
                + str(record_count)
                + "&firstRecord="
                + str(record_start)
            )
            response = requests.get(url, headers=headers)
            response = response.json()
            records = response["Records"]["records"]["REC"]
            write_records(records, collection)
            record_count = 0

    print("Downloaded all records ")


if __name__ == "__main__":
    if os.path.isdir("data") == False:
        os.mkdir("data")
    os.chdir("data")
    get_wos_refs(False)
