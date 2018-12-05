from django.db import connections
from django.conf import settings
from django.http import HttpResponse
import ast
import os
import urllib.request
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder
from . import utils_wallet


cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))

keypath = os.path.join(os.getcwd(), 'keystore_test1')
wallet = KeyWallet.load(keypath, "test1_Account")
wallet_from = wallet.get_address()
print('keypath: ', keypath)


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
        return data

        # SELECT DISTINCT ON (email) * from users
        # ORDER BY email, id DESC;


def db_query(request, table):
    query = [
        '''
        SELECT * FROM users, transaction
        WHERE transaction.wallet = users.wallet
        ORDER BY transaction.timestamp DESC;
        ''',
        '''
        SELECT DISTINCT ON (email) * from users
        ORDER BY email, id DESC
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


def get_highest_gscores(request):
    query = '''
        SELECT users.email, transaction.wallet, transaction.gscore, users.nickname 
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

    try:
        req_body['wallet'] = req_body['wallet']
    except:
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
    que = 'SELECT * from users WHERE user_pid = %s;'
    var_query(que, user_pid)

    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    data = []
    for result in query_result:
        data.append(dict(zip(row_headers, result)))

    return data


def insertDB_transaction(txhash, block, score, wallet, amount, txfee, gscore):
    print('insertDB_transaction')

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
    print('create transfer statistics', request)
    req_body = ast.literal_eval(request.body.decode('utf-8'))

    if req_body['user'] != '*':
        isAll = True
    else:
        isAll = False

    stat_result = {}

    query = [
        '''
        SELECT SUM(transaction.amount),count(transaction.amount)
        FROM transaction,users
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) = (%s) ;
        ''',
        '''
        SELECT date_trunc('day', transaction.timestamp),SUM(transaction.amount), count(transaction.amount)
        FROM transaction,users
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) = (%s)
        GROUP BY date_trunc('day', transaction.timestamp);
        ''',
        '''
        SELECT * FROM users,transaction
        WHERE transaction.wallet = users.wallet
        AND (users.email in (%s)) = (%s)
        ORDER BY transaction.id DESC
        '''
    ]

    stat_result['user'] = req_body['user']

    cursor = connections['default'].cursor()
    cursor.execute(query[0], (req_body['user'], isAll,))
    total = cursor.fetchall()[0]
    stat_result['total_transfer_amount'] = total[0]
    stat_result['total_transfer'] = total[1]

    stat_result['daily'] = []
    cursor.execute(query[1], (req_body['user'], isAll,))
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        stat_result['daily'].append(dict(zip(row_headers, result)))

    stat_result['transaction_list'] = []
    cursor.execute(query[2], (req_body['user'], isAll,))
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        stat_result['transaction_list'].append(dict(zip(row_headers, result)))

    return stat_result
