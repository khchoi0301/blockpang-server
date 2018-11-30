from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.mail import send_mail
from django.conf import settings
from django.db import connections
import ast
import datetime
import json
import os
import urllib.request
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
from . import utils

cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))
recipient = settings.RECIPIENT_LIST
response = {}



def query_transaction(request):
    json_data = []
    query = 'SELECT * FROM transaction;'
    cursor.execute(query)
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()

    for result in query_result:
        json_data.append(dict(zip(row_headers, result)))

    return HttpResponse(str(json_data))


def query_user(request):
    json_data = []
    query = 'SELECT * from users;'
    cursor.execute(query)
    row_headers = [x[0] for x in cursor.description]
    query_result = cursor.fetchall()

    for result in query_result:
        json_data.append(dict(zip(row_headers, result)))

    return HttpResponse(str(json_data))


def index(request):
    page = '<div> Hello Admins: </div>' + str(recipient)
    return HttpResponse(page)


@csrf_exempt  # need to think about security
def create_wallet(request):
    if request.method == 'POST':
        return HttpResponse(utils.create_wallet(request))

@csrf_exempt  # need to think about security
def update_wallet(request):
    if request.method == 'POST':
        return HttpResponse(utils.update_wallet(request))


def transfer_stat(request):
    return HttpResponse(utils.transfer_stat(request))

def user_stat(request):
    return HttpResponse(utils.user_stat(request))


def set_limit(request, amount_limit, block_limit):
    return HttpResponse(utils.set_limit(request, amount_limit, block_limit))


def get_limit(request):
    limit = utils.get_limit()
    limit['amountlimit'] = int(limit['amountlimit'], 16) / 10 ** 18
    limit['blocklimit'] = int(limit['blocklimit'], 16)
    return HttpResponse(str(limit))


def email(minlimit):
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {minlimit} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient)
    print('email has been sent.')
    return HttpResponse('Email has been sent to admins.')


def update_admin(request, cmd, email):
    if cmd == 'add':
        recipient.append(email)
    elif cmd == 'delete':
        recipient.remove(email)

    return HttpResponse(str(recipient))


def get_current_balance(request):
    result = utils.get_block_balance()
    return HttpResponse(
        f'<div>Score: {default_score}</div>\
        <br>\
        <div>Current Balance:</div>\
        <div style="font-weight:bold;">{result}</div>')


@csrf_exempt  # need to think about security
def req_icx(request, to_address, value):

    wallet_icx_maxlimit = 100 * 10 ** 18
    block_icx_warning_minlimit = 10 * 10 ** 18
    value = value

    # if request.method == 'POST':
    #     print('req', request)
    #     print('method', request.method)
    #     req_body = ast.literal_eval(request.body.decode('utf-8'))
    #     value = req_body['value']
    #     print('POST VALUE', value)

    response['block_balance'] = int(utils.get_block_balance(), 16)
    response['wallet_balance'] = int(
        utils.get_wallet_balance(request, to_address), 16)

    # transfer icx
    response['tx_hash'] = utils.send_transaction(request, to_address, value)

    # Add transaction_result key to result
    response['tx_result'] = utils.get_transaction_result(response['tx_hash'])
    if (str(response['tx_result']['status']) == 0):
        response['transaction_result'] = 'failed'
    else:
        response['transaction_result'] = 'success'
    
    print(response['tx_result'])

    # Add game_score key to result
    response['game_score'] = None

    # send a email to admin when block doesn't have enough icx
    if (response['block_balance'] < block_icx_warning_minlimit):
        # call send_email function
        email(str(block_icx_warning_minlimit))
        return HttpResponse(
            'Not enough icx in block - block_icx_warning_minlimit : ' + \
            block_limit)

    # transfer icx only when wallet's balance is under the limit
    if (response['wallet_balance'] > wallet_icx_maxlimit):
        return HttpResponse('You have too much icx in your wallet!!')

    # Check result
    response['block_address'] = default_score
    response['wallet_address'] = to_address
    response['wallet_latest_transaction'] = int(utils.get_latest_transaction(
        request, to_address), 16)
    response['latest_block_height'] = int(utils.get_latest_block_height(), 16)
    response['latest_block_info'] = utils.get_latest_block()
    response['block_balance'] = int(utils.get_block_balance(), 16)
    response['wallet_balance'] = int(
        utils.get_wallet_balance(request, to_address), 16)

    if not response['tx_result']['eventLogs']:
        print(response['tx_result']['failure'])
    else:
        insertDB_transaction(
            response['tx_result']['txHash'], response['tx_result']
            ['blockHeight'], default_score, to_address, value*0.1, 0.0001)

    # Update game_score
    if request.method == 'POST':
        req_body = ast.literal_eval(request.body.decode('utf-8'))
        response['game_score'] = req_body['game_score']

    result_page = {
        'wallet_balance': str(response['wallet_balance']),
        'latest_transaction': str(response['wallet_latest_transaction']),
        'transaction_result': response['transaction_result'],
        'game_score': response['game_score']
        }

    return HttpResponse(str(result_page))
