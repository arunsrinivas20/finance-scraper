import re
import numpy as np

MONTH_TO_NUM = {
    'Jan': 1,
    'Feb': 2,
    'Mar': 3,
    'Apr': 4,
    'May': 5,
    'Jun': 6,
    'Jul': 7,
    'Aug': 8,
    'Sep': 9,
    'Oct': 10,
    'Nov': 11,
    'Dec': 12,
    'January': 1,
    'February': 2,
    'March': 3,
    'April': 4,
    'June': 6,
    'July': 7,
    'August': 8,
    'September': 9,
    'October': 10,
    'November': 11,
    'December': 12
}

def valid_transaction_or_header(id_str):
    if re.match(r"^transaction-\d+$", id_str) or id_str.startswith('header-date-'):
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