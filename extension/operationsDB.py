import sqlite3

conn = None
cursor = None

def close_conn_db():
    conn.close()

def commit_db():
    conn.commit()

def insert_into_db(item, source):
    if (source == 'C1'):
        cursor.execute(f'''INSERT INTO CAPITAL_ONE (transaction_id) VALUES (?);''', (item,))
    elif (source == 'Venmo'):
        cursor.execute(f'''INSERT INTO VENMO (transaction_html) VALUES(?);''', (item,))

def select_from_db(key, source):
    query_result = None

    if (source == 'C1'):
        cursor.execute(f'''SELECT * FROM CAPITAL_ONE WHERE transaction_id = (?);''', (key,))
        query_result = cursor.fetchone()
    elif (source == 'Venmo'):
        cursor.execute(f'''SELECT * FROM VENMO WHERE transaction_html = (?);''', (key,))
        query_result = cursor.fetchone()

    return query_result

def init_db():
    global conn, cursor

    conn = sqlite3.connect('transactions.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS CAPITAL_ONE (
                        transaction_id INTEGER PRIMARY KEY
                    );''')
            
    cursor.execute('''CREATE TABLE IF NOT EXISTS VENMO (
                        transaction_html TEXT PRIMARY KEY
                    )''')
            
    cursor.execute('''CREATE TABLE IF NOT EXISTS CATEGORIES (
                        item TEXT PRIMARY KEY, 
                        category TEXT
                    );''')
                    
    conn.commit()