# collaborator_reports

Collaborator Reports

This package will generate collaborator reports for funding agencies from
CaltechAUTHORS.

Requires: 

Python 3 and the requirements defined in the requirements.txt file (e.g. `pip install -r /path/to/requirements.txt`).

## NSF Collaborator Report

Find the identifier of the individual you want to run a report on. This can be
a Caltech Library person identifier (listed at
https://feeds.library.caltech.edu/people/) or an ORCID identifier.

Type the following command in the terminal:

```bash
python authors_nsf_table4.py <identifier>
```

Where `<identifier>` is the identifier of the individual you want to run a report

This will generate a file <identifier>_nsf_collaborator_report.xlsx with the contents of
table 4 part A.

If you want the CaltechAUTHORS identifiers for each author to trackback
problems, add the `--record_ids` flag:

```bash
python authors_nsf_table4.py <identifier> --record_ids
```

