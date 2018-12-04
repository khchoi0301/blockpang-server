from django.db import connections
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import ast
import datetime
import os
import urllib.request
import time
from iconsdk.wallet.wallet import KeyWallet
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import (
    TransactionBuilder,
    DeployTransactionBuilder,
    CallTransactionBuilder,
    MessageTransactionBuilder
)

cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))

keypath = os.path.join(os.path.dirname(__file__), 'iconkeystore2')
wallet = KeyWallet.load(keypath, "@icon222")
wallet_from = wallet.get_address()


def db_query(request, table):
    query = [
        '''
        SELECT * FROM users, transaction
        WHERE transaction.wallet = users.wallet
        ORDER BY transaction.timestamp DESC
        ;''',
        '''
        SELECT * from users
        ORDER BY id DESC
        ;''',
        'SELECT * FROM transaction;',
        '''
        SELECT * FROM users, transaction
        WHERE transaction.wallet = users.wallet
        AND transaction.timestamp > current_date
        ORDER BY transaction.timestamp DESC
        '''
    ]

    data = []

    if (table == 'transaction'):
        print('===querying transactionDB===')
        cursor.execute(query[0])
    elif (table == 'users'):
        print('===querying usersDB===')
        cursor.execute(query[1])
    elif (table == 'transaction_without_user'):
        print('===querying transactionDB_without_user===')
        cursor.execute(query[2])
    elif (table == 'today'):
        print('===querying todaysDB===')
        cursor.execute(query[3])

    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        data.append(dict(zip(row_headers, result)))
    return data


def get_admins():
    staff_list = []
    staffs = User.objects.filter(is_staff=True).values_list('email', flat=True)
    for staff in staffs:
        staff_list.append(staff)
    print(f'List of staffs: {staff_list}')
    return staff_list


def email(minlimit):
    recipient = get_admins()
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {minlimit} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient)
    print('===SUCCESS: email has been sent.===')
    print(recipient)
    return 'Email has been sent to admins.'


def update_admin(request):
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    username = req_body['username']

    if req_body['cmd'] == 'add':
        new_email = req_body['email']
        try:
            print('not in staff list', req_body)
            new_staff = User.objects.create_user(
                username=req_body['username'],
                password=req_body['password'],
                email=new_email
            )
            new_staff.is_superuser = True
            new_staff.is_staff = True
            new_staff.save()
            print(f'===SUCCESS: {new_email} has been added.===')
            log = f'SUCCESS: {new_email} has been added to admin list.'

        except IntegrityError:
            print(f'===ERROR: {new_email} is already in admin list.===')
            log = f'ERROR: {new_email} is already in admin list.'

    elif req_body['cmd'] == 'delete':
        try:
            User.objects.get(
                username=req_body['username'], is_superuser=True).delete()
            print(f'===SUCCESS: {username} has been deleted.===')
            log = f'SUCCESS: {username} has been deleted from admin list.'

        except ObjectDoesNotExist:
            print(f'===ERROR: {username} is not in admin list.===')
            log = f'ERROR: {username} is not in admin list.'

    return {'staff_list': get_admins(), 'logger': log}


def get_highest_gscores(request):
    query = '''
        SELECT users.email, transaction.wallet, transaction.gscore 
        FROM transaction, users
        WHERE transaction.gscore is NOT NULL 
        AND transaction.wallet = users.wallet
        ORDER BY gscore DESC
        limit 10;
    '''

    data = []
    cursor.execute(query)
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()
    for result in query_result:
        data.append(dict(zip(row_headers, result)))
    return data


def create_wallet(request):
    new_wallet = {}

    wallet = KeyWallet.create()
    new_wallet['address'] = wallet.get_address()
    new_wallet['key'] = wallet.get_private_key()

    insertDB_users(request, new_wallet['address'])
    return new_wallet


def update_wallet(request):
    try:
        return insertDB_users(request, 'include wallet address')
    except Exception as e:
        return {'status': 'fail', 'error_log': str(e)}


def insertDB_users(request, wallet):
    print('insertDB_users func called', request, wallet)
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
    return '===SUCCESS: users DB has been updated==='


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
    return '===SUCCESS: transaction DB has been updated==='


def get_limit():
    '''Get limits.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_limit')\
        .build()

    limit = icon_service.call(call)
    limit['amountlimit'] = int(limit['amountlimit'], 16) / 10 ** 18
    limit['blocklimit'] = int(limit['blocklimit'], 16)

    return limit


def set_limit(request, amount_limit, block_limit):
    '''Set a max amount and frequency of icx Score can send to user.'''
    limit_setting = {}
    limit_setting['amount_limit'] = amount_limit
    limit_setting['block_limit'] = block_limit

    set_limit = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method('set_limit')\
        .params({'amountlimit': amount_limit, 'blocklimit': block_limit})\
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(set_limit, wallet)

    # Sends the transaction
    tx_hash = str(icon_service.send_transaction(signed_transaction))
    print('set_limit complete', tx_hash)  # added
    return limit_setting


def get_wallet_balance(request, to_address):
    '''Get a wallet balance.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_to')\
        .params({'_from': wallet_from, '_to': to_address})\
        .build()
    return int(icon_service.call(call), 16) / 10 ** 18


def send_transaction(request, to_address, value):
    '''Send icx to a wallet.'''
    print('transaction called')

    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method('send_icx')\
        .params({'_to': to_address, 'value': value})\
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    print('transaction complete')

    # Sends the transaction
    return icon_service.send_transaction(signed_transaction)


def get_latest_transaction(request, to_address):
    '''Get a wallet's latest transaction.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('find_transaction')\
        .params({'_to': to_address})\
        .build()
    return int(icon_service.call(call), 16)


def get_latest_block_height():
    '''Get the latest block's height.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('block_height')\
        .build()
    return int(icon_service.call(call), 16)


def get_latest_block():
    '''Get the latest block.'''
    return icon_service.get_block('latest')


def get_transaction_result(tx_hash):
    # check the transaction result
    try:
        time.sleep(6)
        print('6s')
        tx_result = icon_service.get_transaction_result(tx_hash)

    except:
        time.sleep(6)
        print('12s')
        try:
            tx_result = icon_service.get_transaction_result(tx_hash)
        except:
            tx_result = {'failure': {
                'code': '0x7d65',
                'message': "Please wait for few blocks to be created \
                before requesting again"}}

    return tx_result


def get_block_balance():
    '''Get a block's balance.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_balance')\
        .build()
    return int(icon_service.call(call), 16) / 10 ** 18


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


# def user_stat(request):
#     print('create users statistics', request)
#     stat_result = {}

#     query = [
#         '''SELECT COUNT(wallet) FROM users''',
#         '''
#             SELECT service_provider, COUNT(wallet) FROM users
#             GROUP BY service_provider
#         ''',
#         '''
#             SELECT service_provider,date_trunc('day', timestamp), COUNT(*)
#             FROM users
#             GROUP BY service_provider, date_trunc('day', timestamp)
#         '''
#     ]

#     cursor.execute(query[0])
#     stat_result['total_users'] = cursor.fetchall()[0][0]

#     stat_result['total_users_by_pid'] = []
#     cursor.execute(query[1])
#     row_headers = [x[0] for x in cursor.description]
#     query_result = cursor.fetchall()
#     for result in query_result:
#         stat_result['total_users_by_pid'].append(
#             dict(zip(row_headers, result)))

#     stat_result['daily_users'] = []
#     cursor.execute(query[2])
#     row_headers = [x[0] for x in cursor.description]
#     query_result = cursor.fetchall()
#     for result in query_result:
#         stat_result['daily_users'].append(dict(zip(row_headers, result)))

#     return stat_result
