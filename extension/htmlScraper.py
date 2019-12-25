from bs4 import BeautifulSoup
import pandas as pd
from utils import MONTH_TO_NUM, valid_transaction_or_header
import datetime

NAME = 'Arun Srinivas'

def parse_from_C1(html_str):
    transactions = []
    
    curr_year = datetime.datetime.now().year

    soup = BeautifulSoup(html_str, features='lxml')
    html_transactions = soup.find_all("div", id=lambda x: x and valid_transaction_or_header(x))

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

            t_id = html.get_attribute_list('id')[0].split('-')[-1]

            transactions.append({
                'date': f'{month}/{day}/{curr_year % 100}',
                'description': description,
                'amount': -1 * magnitude if is_pos else magnitude,
                'balance': balance,
                'transaction_id': t_id
            })

    return transactions

def determine_venmo_category(desc):
    return ''

def create_venmo_reason(p1, p2, pay_type, desc):
    reason = ''

    if p1 == NAME:
        if pay_type == 'paid':
            reason = f'Paid {p2} for {desc}'
        else: # it's 'charged'
            reason = f'Paid back by {p2} for {desc}'
    else:
        if pay_type == 'paid':
            reason = f'Paid back by {p1} for {desc}'
        else: # it's 'charged'
            reason = f'Paid {p1} for {desc}'

    return reason

def parse_from_Venmo(html_str):  
    soup = BeautifulSoup(html_str, features='lxml')
    html_transactions = soup.find_all("div", {'class': 'feed-story-payment'})
    transactions = []
    
    for html in html_transactions:
        people_div = html.find("div", {'class': 'feed-description__notes'})
        (person1, person2) = tuple([ele.text.strip() for ele in people_div.find_all('strong')])
        pay_type = people_div.find('span').text.strip()

        amount_str = html.find('div', {'class': 'feed-description__amount'}).find('span').text.strip()
        amount = float(amount_str.replace('$', '').replace(',', ''))
        
        # Will be empty for transactions like uber and ubereats. Need to figure out alternatives
        description = html.find('div', {'class': 'feed-description__notes__content'}).text.strip()
        reason = create_venmo_reason(person1, person2, pay_type, description)

        date_str = html.find('span', {'class': 'feed-description__notes__meta'}).find('span').text.strip()
        date_lst = date_str.replace(',', '').split()
        date = f'{MONTH_TO_NUM[date_lst[0]]}/{date_lst[1]}/{int(date_lst[2]) % 100}'

        category = determine_venmo_category(description)

        transactions.append({
            'date': date,
            'description': reason,
            'amount': amount,
            'category': category,
            'html': str(html)
        })

    return transactions
