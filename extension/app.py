from flask import Flask
from flask import request
import json
import re
import pandas as pd
import datetime
from openpyxl import load_workbook
import numpy as np
from decimal import Decimal
from xlrd import XLRDError
import smtplib, ssl, email
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

app = Flask(__name__)
app.debug = True

FILE_PATH = ''
SHEET_NAME = ''
TABLE_NAME = ''
FINANCIAL_INSTITUTION = ''

def is_valid_email(email):
    if re.match(r"^\s*[^@\s]+@[^@\s]+\.[^@\s][^@\s]+\s*$", email):
        return True
    return False

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

def create_transactions_dataframe(finances_sheet, request_string, email):
    filtered_string = request_string.replace('\\', '')
    table_column_location = 0
    start_row = 0
    last_transaction_date = None
    transactions = json.loads(filtered_string)
    num_transactions = len(transactions)
    current_balance = 0
    positive_statements = 0
    negative_statements = 0
    
    if (email == 'undefined'):
        while (finances_sheet.loc[0, table_column_location + 1] != TABLE_NAME):
            table_column_location += 1

        start_row = find_start_row(finances_sheet, table_column_location + 1)
        current_balance = round(finances_sheet.loc[start_row - 1, table_column_location + 1], 2)

        print(finances_sheet)

        last_transaction_date = (finances_sheet.loc[start_row - 1, table_column_location]).date()

        print(last_transaction_date)

    # This will change depending on the structure of your sheet
    columns_to_modify = [table_column_location, table_column_location + 1, table_column_location + 2, table_column_location + 3]

    new_transactions = pd.DataFrame(columns=columns_to_modify)

    for i in range(num_transactions - 1, -1, -1):
        trans_i = transactions[str(i)]

        final_date_obj = pd.to_datetime(trans_i['date']).date()

        if (email != 'undefined' or final_date_obj > last_transaction_date):
            reason = trans_i['description']

            # For all the new transactions, add up the positives and negatives individually and then alert that to the user
            str_amount = trans_i['amount'].replace(',', '')
            float_amount = float(str_amount)

            if (float_amount >= 0):
                positive_statements += float_amount
            else:
                negative_statements += float_amount

            str_balance = None

            if (FINANCIAL_INSTITUTION == 'C1'):
                str_balance = trans_i['balance'].replace(',', '')
            elif (FINANCIAL_INSTITUTION == 'Venmo'):
                current_balance += float_amount
                str_balance = str(current_balance)

            # Figure out how to determine the category for Venmo

            new_transaction = pd.DataFrame([[final_date_obj, str_balance, str_amount, reason]], columns=columns_to_modify)            
            new_transactions = new_transactions.append(new_transaction, ignore_index=True)

    new_transactions[table_column_location + 1] = new_transactions[table_column_location + 1].astype(float)
    new_transactions[table_column_location + 2] = new_transactions[table_column_location + 2].astype(float)

    print(new_transactions)

    return {
        'new_transactions': new_transactions,
        'start_row': start_row,
        'table_column_location': table_column_location,
        'positive_statements': round(positive_statements, 2),
        'negative_statements': round(negative_statements, 2)
    }

def write_to_existing_Excel(request_string, email):
    finances_sheet = None

    try:
        finances_sheet = pd.read_excel(FILE_PATH, sheet_name=SHEET_NAME, header=None)
    except FileNotFoundError:
        return 'No Excel file exists at the path: "{}".'.format(FILE_PATH)
    except XLRDError:
        return 'No Excel sheet by the name of "{}" exists in your Excel File.'.format(SHEET_NAME)
    except:
        return 'Something went wrong. Please check your inputs and try again.'

    dataframe_info = create_transactions_dataframe(finances_sheet, request_string, email)

    new_transactions = dataframe_info['new_transactions']
    start_row = dataframe_info['start_row']
    table_column_location = dataframe_info['table_column_location']

    append_to_existing_Excel_sheet(new_transactions.round(2), start_row, table_column_location)

    return len(new_transactions)

def send_email(email, positive_statements, negative_statements):
    port = 465  
    net_spend = round(positive_statements + negative_statements, 2)
    abs_net_spend = abs(net_spend)
    body = f"""
        Dear Account Holder,

        Attached in this email is a list of the recent transactions you had in your {FINANCIAL_INSTITUTION} account.

        Your positive transactions amounted to ${positive_statements}.
        Your negative transactions amounted to {'-' if negative_statements < 0 else ''}${negative_statements * -1}.

        Overall, your net spending for these recent transactions was {'-' if net_spend < 0 else ''}${abs_net_spend}.

        Thank you.
    """

    # Using a throwaway email for now, but this could be turned into an input where the
    # user emails themself the excel file
    password = 'Soccer#123'

    message = MIMEMultipart()
    message["To"] = email
    message["Subject"] = f'Your Recent {FINANCIAL_INSTITUTION} Transactions'

    message.attach(MIMEText(body, "plain"))

    filename = "transactions.xlsx" 

    with open(filename, "rb") as attachment:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename= {filename}")

    message.attach(part)
    text = message.as_string()

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login("emailservicedev@gmail.com", password)
        server.sendmail("emailservicedev@gmail.com", email, text)

def email_transactions_dataframe(request_string, email):
    if (not is_valid_email(email)):
        return '"{}" is not valid email. Please try again.'.format(email)

    dataframe_info = create_transactions_dataframe(None, request_string, email)

    new_transactions = dataframe_info['new_transactions']
    positive_statements = dataframe_info['positive_statements']
    negative_statements = dataframe_info['negative_statements']

    new_transactions_renamed = new_transactions.rename(columns={
        0: 'Date',
        1: 'Balance',
        2: 'Amount',
        3: 'Reason'
    })

    writer = pd.ExcelWriter('./transactions.xlsx', engine='openpyxl', date_format='m/d/yy')
    new_transactions_renamed.to_excel(writer, 'Sheet1', float_format='%.2f', header=True, index=False)
    writer.save()

    send_email(email, positive_statements, negative_statements)

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

    FILE_PATH = request.form['file_path']
    SHEET_NAME = request.form['excel_sheet']

    fin_inst = request.form['financial_institution']
    if ('Capital One' in fin_inst):
        FINANCIAL_INSTITUTION = 'C1'
    elif ('Venmo' in fin_inst):
        FINANCIAL_INSTITUTION = 'Venmo'

    email = request.form['email'].strip()

    number_of_new_transactions = None

    if (FINANCIAL_INSTITUTION == 'C1'):
        TABLE_NAME = 'Bank'
    elif (FINANCIAL_INSTITUTION == 'Venmo'):
        TABLE_NAME = 'Venmo'

    if (TABLE_NAME != ''):
        if (email != 'undefined'):
            number_of_new_transactions = email_transactions_dataframe(request.form['data'], email)
        else:
            number_of_new_transactions = write_to_existing_Excel(request.form['data'], email)
    
    if (not is_number(number_of_new_transactions)):
        return number_of_new_transactions

    message = None

    if (email == 'undefined'):
        message = construct_alert_message(number_of_new_transactions)
    else:
        message = 'An Excel Workbook containing '
        if (number_of_new_transactions == 1):
            message += '1 new transaction '
        else:
            if (number_of_new_transactions == 0):
                message += 'no new transactions '
            else:
                message += str(number_of_new_transactions) + ' new transactions '
        
        message += 'was sent to "{}."'.format(email)

    return message

if __name__ == "__main__":
    app.run()
    