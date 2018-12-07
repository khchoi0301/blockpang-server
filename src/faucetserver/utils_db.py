from django.db import connections
from django.conf import settings
from django.http import HttpResponse
import ast
import os
import urllib.request
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder
from . import utils_admin, utils_wallet


cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))
wallet = settings.WALLET
wallet_from = settings.WALLET_FROM


def db_query(table):
    query = [
        '''
        SELECT * FROM users, transaction
        WHERE transaction.wallet = users.wallet
        ORDER BY transaction.timestamp DESC;
        ''',
        '''
        SELECT DISTINCT ON (user_pid) * from users
        ORDER BY  user_pid, id DESC;
        ''',
        '''
        SELECT count(transaction.block) as total_transfer,
        sum(transaction.amount) as total_transfer_amount
        FROM transaction, users
        WHERE transaction.wallet = users.wallet;
        ''',
        '''
        SELECT users.email, users.nickname,
        transaction.wallet, transaction.gscore
        FROM transaction, users
        WHERE transaction.gscore is NOT NULL 
        AND transaction.wallet = users.wallet
        ORDER BY gscore DESC
        limit 10;
        '''
    ]

    if (table == 'transaction'):
        print('===querying transactionDB===')
        return execute_query(query=query[0])
    elif (table == 'users'):
        print('===querying usersDB===')
        return execute_query(query=query[1])
    elif (table == 'summary'):
        print('===querying summary===')
        return execute_query(query=query[2], table='summary')
    elif (table == 'leaderboard'):
        print('===querying leaderboard===')
        return execute_query(query=query[3])


def transfer_stat(request):
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    query = [
        '''
        SELECT SUM(transaction.amount),count(transaction.amount)
        FROM transaction,users
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) = (%s) ;
        ''',
        '''
        SELECT date_trunc('month', transaction.timestamp),
        date_trunc('month', transaction.timestamp) as month,
        SUM(transaction.amount), count(transaction.amount)
        FROM transaction,users
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) = (%s)
        GROUP BY date_trunc('month', transaction.timestamp)
        ORDER BY date_trunc('month', transaction.timestamp) DESC;
        ''',
        '''
        SELECT date_trunc('day', transaction.timestamp),
        SUM(transaction.amount), count(transaction.amount)
        FROM transaction,users
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) = (%s)
        GROUP BY date_trunc('day', transaction.timestamp)
        ORDER BY date_trunc('day', transaction.timestamp) DESC;
        ''',
        '''
        SELECT transaction.*, users.email FROM users,transaction
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) 
        ORDER BY transaction.id DESC
        '''
    ]

    if req_body['user'] != '*':
        isAll = True
    else:
        isAll = False

    return execute_stat_query(req_body=req_body, query=query, isAll=isAll)


# Insert a new row to users table
def insertDB_users(request, wallet):
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    req_body['wallet'] = wallet

    query = '''
        INSERT INTO users 
        (service_provider, wallet, email, user_pid, profile_img_url, nickname) 
        VALUES (%s,%s,%s,%s,%s,%s)
        '''

    cursor.execute(query, (
        req_body['service_provider'], req_body['wallet'], req_body['email'],
        req_body['user_pid'], req_body['profile_img_url'],
        req_body['nickname']))

    connections['default'].commit()

    user_pid = req_body['user_pid']
    que = 'SELECT * from users WHERE user_pid = %s ORDER BY id DESC;'
    return execute_query(query=que, var=user_pid)[0]


# Insert a new row to transaction table
def insertDB_transaction(txhash, block, score, wallet, amount, txfee, gscore):
    query = '''
        INSERT INTO transaction 
        (txhash, block, score, wallet, amount, txfee, gscore) 
        VALUES (%s,%s,%s,%s,%s,%s,%s)
        '''
    cursor.execute(query, (txhash, block, score,
                           wallet, amount, txfee, gscore))

    connections['default'].commit()

    que = 'SELECT * from transaction WHERE txhash = %s;'
    return execute_query(query=que, var=txhash)


# A helper function called by db_query
def execute_query(**kwargs):
    if ('var' in kwargs):
        var = kwargs['var']
        cursor.execute(kwargs['query'], (var,))
    else:
        cursor.execute(kwargs['query'])

    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    data = []

    for result in query_result:
        data.append(dict(zip(row_headers, result)))

    if ('table' not in kwargs):
        return data
    else:
        data = data[0]
        data['total_user'] = len(db_query('users'))
        data['score_address'] = default_score
        data['current_balance'] = utils_wallet.get_block_balance()
        data['admin_email'] = utils_admin.get_admins()
        return data

# A helper function called by transfer_stat
def execute_stat_query(**kwargs):
    req = kwargs['req_body']
    query = kwargs['query']
    isAll = kwargs['isAll']

    data = {}
    data['user'] = req['user']
    data['monthly'] = []
    data['daily'] = []
    data['transaction_list'] = []

    cols = ['', 'monthly', 'daily', 'transaction_list']
    
    for n in range(1,4):
        current_query = query[n]
        if n == 3:
            cursor.execute(current_query, (req['user'], ))
        else:
            cursor.execute(current_query, (req['user'], isAll,))
        row_headers = [x[0] for x in cursor.description]
        query_result = cursor.fetchall()
        for result in query_result:
            data[cols[n]].append(dict(zip(row_headers, result)))
    
    for result in data['monthly']:
        result['month'] = result['month'].month
    cursor.execute(query[0], (req['user'], isAll,))
    total = cursor.fetchall()[0]
    data['total_transfer_amount'] = total[0]
    data['total_transfer'] = total[1]

    return data

