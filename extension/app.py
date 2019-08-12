from flask import Flask
from flask import request
import json
import pandas as pd
import datetime
from openpyxl import load_workbook
import numpy as np
from decimal import Decimal

app = Flask(__name__)
app.debug = True

# MAKE SURE TO MODIFY TO MATCH YOUR OWN EXCEL FILE
# TABLE_NAME IS ASSIGNED DYNAMICALLY BELOW
FILE_PATH = '/Users/asrini19/Documents/Finances.xlsx'
SHEET_NAME = 'Bank and Venmo'
TABLE_NAME = ''

def is_number(number):
    try:
        float(number)
        return True
    except ValueError:
        return False

def find_start_row(dataframe, table_column_location):
    row = 0
    no_empty_cell = True
    while (no_empty_cell):
        value = dataframe.loc[row, table_column_location]
        no_empty_cell = not (is_number(value) and (np.isnan(value) or value == 0))
        if (no_empty_cell):
            row += 1

    return row

def append_to_existing_Excel_sheet(dataframe, start_row, table_column_location):
    np.round(dataframe, decimals=2)

    book = load_workbook(FILE_PATH)
    excel_writer = pd.ExcelWriter(FILE_PATH, engine='openpyxl', date_format='m/d/yy') 
    excel_writer.book = book
    excel_writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

    dataframe.to_excel(excel_writer, sheet_name=SHEET_NAME, float_format='%.2f', header=False, index=False, startrow=start_row, startcol=table_column_location)

    # Uncomment the line below whenever you want to write to desired Excel file
    excel_writer.save()

def create_transactions_dataframe(request_string, financial_institution):
    filtered_string = request_string.replace('\\', '')
    table_column_location = 0
    transactions = json.loads(filtered_string)
    num_transactions = len(transactions)

    finances_sheet = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=None)

    while (finances_sheet.loc[0, table_column_location + 1] != TABLE_NAME):
        table_column_location += 1

    # This will change depending on the structure of your sheet
    columns_to_modify = [table_column_location, table_column_location + 1, table_column_location + 2, table_column_location + 3]

    start_row = find_start_row(finances_sheet, table_column_location + 1)
    current_balance = round(finances_sheet.loc[start_row - 1, table_column_location + 1], 2)

    print(finances_sheet)

    last_transaction_date = (finances_sheet.loc[start_row - 1, table_column_location]).date()

    print(last_transaction_date)

    new_transactions = pd.DataFrame(columns=columns_to_modify)

    for i in range(num_transactions - 1, -1, -1):
        trans_i = transactions[str(i)]

        final_date_obj = pd.to_datetime(trans_i['date']).date()

        if (final_date_obj > last_transaction_date):
            reason = trans_i['description']

            # For all the new transactions, add up the positives and negatives individually and then alert that to the user
            str_amount = trans_i['amount'].replace(',', '')

            str_balance = None

            if (financial_institution == 'C1'):
                str_balance = trans_i['balance'].replace(',', '')
            elif (financial_institution == 'Venmo'):
                current_balance += float(str_amount)
                str_balance = str(current_balance)

            # Figure out how to determine the category

            new_transaction = pd.DataFrame([[final_date_obj, str_balance, str_amount, reason]], columns=columns_to_modify)            
            new_transactions = new_transactions.append(new_transaction, ignore_index=True)

    new_transactions[table_column_location + 1] = new_transactions[table_column_location + 1].astype(float)
    new_transactions[table_column_location + 2] = new_transactions[table_column_location + 2].astype(float)

    print(new_transactions)

    append_to_existing_Excel_sheet(new_transactions.round(2), start_row, table_column_location)

    return len(new_transactions) 
 
@app.route("/", methods=['POST'])
def index():
    global TABLE_NAME

    if (request.form['data'] == 'undefined'):
        return 'Something went wrong. We were not able to find any transactions.'

    number_of_new_transactions = None
    financial_institution = request.form['financial_institution']

    if ('Capital One' in financial_institution):
        TABLE_NAME = 'Bank'
        number_of_new_transactions = create_transactions_dataframe(request.form['data'], 'C1')
    elif ('Venmo' in financial_institution):
        TABLE_NAME = 'Venmo'
        number_of_new_transactions = create_transactions_dataframe(request.form['data'], 'Venmo')

    alert_message = None

    if (number_of_new_transactions == 1):
        alert_message = '1 New Transaction Was Recorded'
    else:
        alert_message = ' New Transactions Were Recorded'
        if (number_of_new_transactions == 0):
            alert_message = 'No' + alert_message
        else:
            alert_message = str(number_of_new_transactions) + alert_message

    if ('Capital One' in financial_institution):
        alert_message += ' from Your Capital One Account'
    elif ('Venmo' in financial_institution):
        alert_message += ' from Your Venmo Account'

    return alert_message

if __name__ == "__main__":
    app.run()