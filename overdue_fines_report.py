from datetime import datetime
from os import mkdir, path
# from src.folioApi import FolioApi
import folioclient
import logging
import csv
import email_charges

# folio = FolioApi()
folio = folioclient.FolioClient(
    okapi_url='https://okapi-umsystem.folio.ebsco.com',
    tenant_id='fs00001083',
    username='jrb7f0',
    password='FF247tb30!'
)

todays_date_iso_8601_ext = datetime.today().strftime('%Y-%m-%d')
todays_date_iso_8601_basic = datetime.today().strftime('%Y%m%d')

logfile=F"logs/overdue_fines_report_{todays_date_iso_8601_basic}.log"
if not path.isdir('logs'):
    mkdir('logs')
# Set up log file
logging.basicConfig(filename=logfile, level=logging.DEBUG, force=True, format='%(asctime)s %(message)s')
logging.info(F"{todays_date_iso_8601_ext}")

# Get all locations as a list of location objects
LOCATIONS = folio.locations
# LOCATIONS = folio.folio_get(
#     'locations',
#     key='locations',
#     query_params={'limit': 9999}
# )
# LOCATIONS = folio.session.get(
#     folio.okapi_url + '/locations', 
#     params={'limit': 9999}
#     ).json()['locations']

umkc_campus_id = "7db96b4b-ccfe-45a8-b619-f44d8d28a726"
UMKC_SERVICEPOINTS = [
    srvPtId for loc
    in LOCATIONS
    if loc['campusId'] == umkc_campus_id for srvPtId in loc['servicePointIds']
]
print(F"Get Open loans with due date before {todays_date_iso_8601_ext}")
query = """
    status.name = 'Open' 
    and 
    dueDate < {}
    sortby metadata.updatedDate desc
""".format(todays_date_iso_8601_ext)

# url = folio.okapi_url + '/circulation/loans'
# url = folio.okapi_url + '/circulation/loans'
# print("GET:", url)
rsp = folio.folio_get('circulation/loans', query_params={'limit': 0, 'offset': 0, 'query': query})
total_records = rsp.get('totalRecords')
# resp = folio.session.get(url, params={'query': query, 'limit': 0, 'offset': 0})
# total_records = resp.json()['totalRecords']
print("total_records:", total_records)
offset = 0
limit = 250
loans = []
while offset <= total_records:
    resp = folio.folio_get(
        'circulation/loans',
        key='loans',
        query_params={'limit': limit, 'offset': offset, 'query': query}
    )
    loans.extend(resp)
    # resp = folio.session.get(
    #     url, 
    #     params={
    #         'query': query,
    #         'limit': limit,
    #         'offset': offset
    #         }
    #     )
    # if resp.ok:
    #     loans.extend(resp.json()['loans'])
    offset += limit
# Get open loans scoped to UMKC campus
umkc_loans = [
    loan for loan 
    in loans
    if loan['checkoutServicePointId'] in UMKC_SERVICEPOINTS
]
# print("umkc_loans:", umkc_loans)
print("umkc_loans:", len(umkc_loans))

# get rows from loans
rows = []
for ln in umkc_loans:
    logging.info(F"{ln}")
    borrower = ln.get('borrower')
    firstName = borrower.get('firstName') or ""
    lastName = ln.get('borrower').get('lastName') or ""
    middleName = ln.get('borrower').get('middleName') or ""
    borrower_name = lastName + ", " + firstName + " " + middleName
    borrower_barcode = ln.get('borrower').get('barcode')
    borrower_id = ln.get('userId')
    # get borrower's email
    user = folio.folio_get(f'users/{borrower_id}') or dict()
    # user = folio.session.get(folio.okapi_url + '/users/' + borrower_id).json() or dict()
    borrower_email = user.get('personal').get('email')
    due_date = ln.get('dueDate')
    loan_date = ln.get('loanDate')
    loan_policy = ln.get('loanPolicy').get('name')
    fee_fine = ln.get('feesAndFines').get('amountRemainingToPay')
    item_title = ln.get('item').get('title')
    material_type = ln.get('item').get('materialType').get('name')
    item_status = ln.get('item').get('status').get('name')
    barcode = ln.get('item').get('barcode')
    callNumberComponents = ln.get('item').get('callNumberComponents')
    if callNumberComponents:
        call_number_prefix = callNumberComponents.get('prefix') or "-"
        call_number_suffix = callNumberComponents.get('suffix') or "-"
    call_number = ln.get('item').get('callNumber') or "-"
    volume = ln.get('item').get('volume') or "-"
    enumeration = ln.get('item').get('enumeration') or "-"
    chronology = ln.get('item').get('chronology') or "-"
    copy_number = ln.get('item').get('copyNumber') or "-"
    contributors = ln.get('item').get('contributors') or []
    contributors = "; ".join([c.get('name') for c in contributors]) or "-"
    location = ln.get('item').get('location').get('name')
    campus = "UMKC"
    instance_id = ln.get('item').get('instanceId')
    holdings_id = ln.get('item').get('holdingsRecordId')
    item_id = ln.get('itemId')
    row = (
        borrower_name, borrower_barcode, borrower_email, campus, 
        borrower_id, due_date, loan_date, loan_policy,
        fee_fine, item_title, material_type, item_status,
        barcode, call_number_prefix, call_number, call_number_suffix,
        volume, enumeration, chronology, copy_number, contributors,
        location, instance_id, holdings_id, item_id
        )
    # print(row)
    rows.append(row)

# sort rows by due date
rows_sorted = sorted(rows, key=lambda x: x[5])

output_file = F"umkc_loans_{todays_date_iso_8601_basic}.csv"
with open(output_file, "w", newline='', encoding="utf-8") as file:
    fw = csv.writer(file)
    # Write headers
    fw.writerow(
        (
            'Borrower name',
            'Borrower barcode',
            'Borrower email',
            'Campus',
            'Borrower ID',
            'Due date',
            'Loan date',
            'Loan policy',
            'Fee/Fine',
            'Item title',
            'Material type',
            'Item status',
            'Barcode',
            'Call number prefix',
            'Call number',
            'Call number suffix',
            'Volume',
            'Enumeration',
            'Chronology',
            'Copy number',
            'Contributors',
            'Location',
            'Instance ID',
            'Holdings ID',
            'Item ID'
        )
    )
    for row in rows_sorted:
        fw.writerow(row)

# email_charges.send_email(
#     sender="",
#     recipients=
# )

output_file = F"umkc_loans_{todays_date_iso_8601_basic}.tsv"
with open(output_file, "w", newline='', encoding="utf-8") as file:
    fw = csv.writer(file, delimiter='\t')
    # Write headers
    fw.writerow(
        (
            'Borrower name',
            'Borrower barcode',
            'Borrower email',
            'Campus',
            'Borrower ID',
            'Due date',
            'Loan date',
            'Loan policy',
            'Fee/Fine',
            'Item title',
            'Material type',
            'Item status',
            'Barcode',
            'Call number prefix',
            'Call number',
            'Call number suffix',
            'Volume',
            'Enumeration',
            'Chronology',
            'Copy number',
            'Contributors',
            'Location',
            'Instance ID',
            'Holdings ID',
            'Item ID'
        )
    )
    for row in rows_sorted:
        fw.writerow(row)
