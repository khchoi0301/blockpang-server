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


def execute_query(**kwargs):
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
        data['score_address'] = default_score
        data['current_balance'] = utils_wallet.get_block_balance()
        data['admin_email'] = utils_admin.get_admins()
        return data


def db_query(table):
    query = [
        '''
        SELECT * FROM users, transaction
        WHERE transaction.wallet = users.wallet
        ORDER BY transaction.timestamp DESC;
        ''',
        '''
        SELECT DISTINCT ON (email, user_pid) * from users
        ORDER BY email, user_pid, id DESC
        ;
        ''',
        '''
        SELECT count(txhash) as total_transfer,
        sum(amount) as total_transfer_amount,
        count(DISTINCT wallet) as total_users
        from transaction;
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


def get_highest_gscores():
    query = '''
        SELECT users.email, users.nickname,
        transaction.wallet, transaction.gscore
        FROM transaction, users
        WHERE transaction.gscore is NOT NULL 
        AND transaction.wallet = users.wallet
        ORDER BY gscore DESC
        limit 10;
    '''

    cursor.execute(query)
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    data = []
    for result in query_result:
        data.append(dict(zip(row_headers, result)))

    return data


def var_query(query, var):
    cursor.execute(query, (var,))


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
    var_query(que, user_pid)

    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    data = []
    for result in query_result:
        data.append(dict(zip(row_headers, result)))

    return data[0]


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
    var_query(que, txhash)

    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    data = []
    for result in query_result:
        data.append(dict(zip(row_headers, result)))

    return data


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
        SELECT * FROM users,transaction
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) 
        ORDER BY transaction.id DESC
        '''
    ]

    if req_body['user'] != '*':
        isAll = True
    else:
        isAll = False

    stat_result = {}

    stat_result['user'] = req_body['user']
    cursor.execute(query[0], (req_body['user'], isAll,))
    total = cursor.fetchall()[0]
    stat_result['total_transfer_amount'] = total[0]
    stat_result['total_transfer'] = total[1]

    stat_result['monthly'] = []
    cursor.execute(query[1], (req_body['user'], isAll,))
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        stat_result['monthly'].append(dict(zip(row_headers, result)))

    for result in stat_result['monthly']:
        result['month'] = result['month'].month

    stat_result['daily'] = []
    cursor.execute(query[2], (req_body['user'], isAll,))
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        stat_result['daily'].append(dict(zip(row_headers, result)))

    stat_result['transaction_list'] = []
    cursor.execute(query[3], (req_body['user'],))
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        stat_result['transaction_list'].append(dict(zip(row_headers, result)))

    return stat_result
