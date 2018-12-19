# collaborator_reports

Collaborator Reports

This package will generate collaborator reports for funding agencies from
various data sources.

Requires: 

Python 3 (Recommended via [Anaconda](https://www.anaconda.com/download)) with reqests library and [Dataset](https://github.com/caltechlibrary/dataset).

## Usage

### WOS-based Report
Get a WOS API token from https://developer.clarivate.com/.  Open a terminal window and save your token by typing `export WOSTOK='TOKEN"`, replacing TOKEN with the actual token.
Search on Web of Science to determine the correct author search term (e.g. Mooley K).
Open a new google sheet and copy the sheet ID (the long random character string between the end /'s in the sheet url). 
Type `python get_articles_wos.py`. 
The script will request the WOS author search term, whether you want to restrict your search to Caltech, and the google sheet id where you want the results to be output. Review this sheet to ensure each article is correct.
This script generates a dataset collection using the last name in the search term (e.g. Mooley.ds)

## Formatting NSF_C_A Report
Once you have reviewed the articles, type `python format_nsf_c_a.py dataset_collection input_google_sheet_id output_google_sheet_id`, where the dataset_collection is from the get_articles step, the input_google sheet is the reviewed spreadsheet with articles, and output_google_sheet is the new sheet where the report fragment will be generated.  An additional option `-limited` limits the results to the first three authore per paper.  This formatting script de-duplicates the authors and generates a formatted report.

## Additional sources
Additional scripts in this repository for ADS and CaltechAUTHORS are from earlier attempts and will all be merged into the above harvest and format approach.
