from flask import Flask
from flask import request
import re
import pandas as pd
import datetime
from openpyxl import load_workbook
import numpy as np
from decimal import Decimal
from xlrd import XLRDError
import sys
import shutil
import os
from htmlScraper import parse_from_C1, parse_from_Venmo
from utils import find_start_row, is_number
from operationsDB import init_db, select_from_db, insert_into_db, commit_db, close_db_conn

# import smtplib, ssl, email
# from email import encoders
# from email.mime.base import MIMEBase
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText

app = Flask(__name__)
app.debug = True

FILE_PATH = ''
SHEET_NAME = ''
TABLE_NAME = ''
FINANCIAL_INSTITUTION = ''

def append_to_existing_Excel_sheet(dataframe, start_row, table_column_location):
    np.round(dataframe, decimals=2)

    book = load_workbook(FILE_PATH)
    excel_writer = pd.ExcelWriter(FILE_PATH, engine='openpyxl', date_format='m/d/yy') 
    excel_writer.book = book
    excel_writer.sheets = dict((ws.title, ws) for ws in book.worksheets)

    dataframe.to_excel(excel_writer, sheet_name=SHEET_NAME, float_format='%.2f', header=False, index=False, startrow=start_row, startcol=table_column_location)

    # Uncomment these 2 lines below whenever you want to write to desired Excel file and commit insertions
    # excel_writer.save()
    # commit_db()


def create_transactions_dataframe(finances_sheet, transactions):
    table_column_location = 0
    start_row = 0
    last_transaction_date = None
    num_transactions = len(transactions)
    columns_to_modify = None
    current_balance = None
    
    while (finances_sheet.loc[0, table_column_location + 1] != TABLE_NAME):
        table_column_location += 1

    start_row = find_start_row(finances_sheet, table_column_location + 1)

    last_transaction_date = (finances_sheet.loc[start_row - 1, table_column_location]).date()
    current_balance = finances_sheet.loc[start_row - 1, table_column_location + 1]

    print(f'LAST RECORDED DATE: {last_transaction_date}')

    # This will change depending on the structure of your sheet
    if (FINANCIAL_INSTITUTION == 'C1'):
        columns_to_modify = [table_column_location, table_column_location + 1, table_column_location + 2, table_column_location + 3]   
    elif (FINANCIAL_INSTITUTION == 'Venmo'):
        columns_to_modify = [table_column_location, table_column_location + 1, table_column_location + 2, table_column_location + 3, table_column_location + 4]

    new_transactions = pd.DataFrame(columns=columns_to_modify)

    for i in range(num_transactions - 1, -1, -1):
        trans_i = transactions[i]

        final_date_obj = pd.to_datetime(trans_i['date']).date()

        # Need to figure out duplicates
        if (final_date_obj >= last_transaction_date):
            new_transaction = None
            values_to_insert = None
            reason = trans_i['description']
            amount = trans_i['amount']
            can_insert = True

            if (FINANCIAL_INSTITUTION == 'C1'):
                if (not select_from_db(trans_i['transaction_id'], 'C1')):
                    balance = trans_i['balance']
                    values_to_insert = [final_date_obj, balance, amount, reason]

                    insert_into_db(trans_i['transaction_id'], 'C1')
                else:
                    can_insert = False
            elif (FINANCIAL_INSTITUTION == 'Venmo'):
                # Venmo does not allow duplicate transactions in the same minute, so
                # we can define a "unique" transaction to be unique based on its
                # date, time, person1, person2, amount, and original (in venmo) description. 
                item = f'{trans_i["date"]} {trans_i["time"]} {trans_i["person1"]} {trans_i["person2"]} {str(amount)} {trans_i["original_reason"]}'

                if (not select_from_db(item, 'Venmo')):
                    current_balance += amount
                    category = trans_i['category']
                    values_to_insert = [final_date_obj, current_balance, amount, reason, category]

                    insert_into_db(item, 'Venmo')
                else:
                    can_insert = False

            if (can_insert):
                new_transaction = pd.DataFrame([values_to_insert], columns=columns_to_modify)
                new_transactions = new_transactions.append(new_transaction, ignore_index=True)

    new_transactions[table_column_location + 1] = new_transactions[table_column_location + 1].astype(float)
    new_transactions[table_column_location + 2] = new_transactions[table_column_location + 2].astype(float)

    print(new_transactions)

    return {
        'new_transactions': new_transactions,
        'start_row': start_row,
        'table_column_location': table_column_location
    }

def write_to_existing_Excel(request_string):
    finances_sheet = None

    try:
        finances_sheet = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=None)
    except FileNotFoundError:
        return 'No Excel file exists at the path: "{}".'.format(FILE_PATH)
    except XLRDError:
        return 'No Excel sheet by the name of "{}" exists in your Excel File.'.format(SHEET_NAME)
    except:
        return 'Something went wrong. Please check your inputs and try again.'

    dataframe_info = create_transactions_dataframe(finances_sheet, request_string)

    new_transactions = dataframe_info['new_transactions']
    start_row = dataframe_info['start_row']
    table_column_location = dataframe_info['table_column_location']

    append_to_existing_Excel_sheet(new_transactions.round(2), start_row, table_column_location)

    return len(new_transactions)

def construct_alert_message(number_of_new_transactions):
    alert_message = None

    if (number_of_new_transactions == 1):
        alert_message = '1 New Transaction Was Recorded'
    else:
        alert_message = ' New Transactions Were Recorded'
        if (number_of_new_transactions == 0):
            alert_message = 'No' + alert_message
        else:
            alert_message = str(number_of_new_transactions) + alert_message

    if (FINANCIAL_INSTITUTION == 'C1'):
        alert_message += ' from Your Capital One Account'
    elif (FINANCIAL_INSTITUTION == 'Venmo'):
        alert_message += ' from Your Venmo Account'

    return alert_message
 
@app.route("/", methods=['POST'])
def index():
    global TABLE_NAME, FILE_PATH, SHEET_NAME, FINANCIAL_INSTITUTION

    if (request.form['data'] == 'undefined'):
        return 'Something went wrong. We were not able to find any transactions.'

    html_data = request.form['data']
    FILE_PATH = request.form['file_path']
    SHEET_NAME = request.form['excel_sheet']
    transactions = None
    fin_inst = request.form['financial_institution']

    init_db()

    if ('Capital One' in fin_inst):
        FINANCIAL_INSTITUTION = 'C1'
        TABLE_NAME = 'Bank'
        transactions = parse_from_C1(html_data)
    elif ('Venmo' in fin_inst):
        FINANCIAL_INSTITUTION = 'Venmo'
        TABLE_NAME = 'Venmo'
        transactions = parse_from_Venmo(html_data)
    else:
        return 'Something went wrong. We were not able to determine your financial institution.'

    number_of_new_transactions = None

    if (TABLE_NAME == 'Bank' or TABLE_NAME == 'Venmo'):
        number_of_new_transactions = write_to_existing_Excel(transactions)
    
    if (not is_number(number_of_new_transactions)):
        return number_of_new_transactions

    close_db_conn()

    return construct_alert_message(number_of_new_transactions)

if __name__ == "__main__":
    if os.path.exists('./__pycache__'):
        shutil.rmtree('./__pycache__')

    app.run()
    