from bs4 import BeautifulSoup
import pandas as pd
from utils import MONTH_TO_NUM, valid_transaction_or_header
import datetime

def parse_from_C1(html_str):
    transactions = []
    
    curr_year = datetime.datetime.now().year

    soup = BeautifulSoup(html_str, features='lxml')
    html_transactions = soup.find_all("div", id=lambda x: x and valid_transaction_or_header(x))

    i = 0
    for html in html_transactions:
        if 'header-date' in html.get_attribute_list('class'):
            curr_year = int(html.get_attribute_list('id')[0].split('-')[-1])
        else:
            month = MONTH_TO_NUM[html.find("div", {"class": "month"}).text]
            day = html.find("div", {"class": "day"}).text
            description = html.find("span", id=lambda x: x and x.startswith('transactionName')).text
            amount = html.find("div", {"class": lambda x: x and x.startswith('transaction-amount ')})
            magnitude = float(amount.text[1:].replace(',', ''))
            is_pos = amount.get_attribute_list('class')[1] == 'Credit'
            balance = float(html.find("div", {"class": "transaction-balance"}).text[1:].replace(',', ''))

            transactions.append({
                'date': f'{month}/{day}/{curr_year % 100}',
                'description': description,
                'amount': -1 * magnitude if is_pos else magnitude,
                'balance': balance
            })

        i += 1

    return transactions

def parse_from_Venmo(html_str):  
    soup = BeautifulSoup(html_str, features='lxml')
    html_transactions = soup.find_all("div", {'class': 'feed-story-payment'})
    print(html_transactions[15])
    
    people = tuple([ele.text for ele in html_transactions[15].find_all("strong")])

    amount_str = html_transactions[15].find('div', {'class': 'feed-description__amount'}).find('span').text
    amount = float(amount_str.replace('$', '').replace(',', ''))
    
    description = html_transactions[15].find('div', {'class': 'feed-description__notes__content'}).text

    date_str = html_transactions[15].find('span', {'class': 'feed-description__notes__meta'}).find('span').text
    date_lst = date_str.replace(',', '').split()
    date = f'{MONTH_TO_NUM[date_lst[0]]}/{date_lst[1]}/{int(date_lst[2]) % 100}'

    print(people, amount, description, date)