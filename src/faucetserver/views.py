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


default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))
recipient = settings.RECIPIENT_LIST


def index(request):
    page = f'<div> Hello Admins: </div>{str(recipient)}'
    return HttpResponse(page)


def db_query(request, table):
    return HttpResponse(utils.db_query(request, table))


def email(minlimit):
    return HttpResponse(utils.email(minlimit))


def update_admin(request, cmd, email):
    return HttpResponse(utils.update_admin(request, cmd, email))


def get_current_balance(request):
    result = utils.get_block_balance()
    return HttpResponse(
        f'<div>Score: {default_score}</div>\
        <br>\
        <div>Current Balance:</div>\
        <div style="font-weight:bold;">{result}</div>')


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


@csrf_exempt  # need to think about security
def req_icx(request):

    response = {}

    wallet_icx_maxlimit = 100 * 10 ** 18
    block_icx_warning_minlimit = 10 * 10 ** 18
    value = 0.1

    # Update game score
    if request.method == 'POST':
        req_body = ast.literal_eval(request.body.decode('utf-8'))
        response['game_score'] = req_body['game_score']
        to_address = req_body['wallet']
        value = int(response['game_score'])

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

    # send a email to admin when block doesn't have enough icx
    if (response['block_balance'] < block_icx_warning_minlimit):
        # call send_email function
        email(str(block_icx_warning_minlimit))
        return HttpResponse(f'Not enough icx in block - \
            block_icx_warning_minlimit : {block_limit}')

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
        utils.insertDB_transaction(
            response['tx_result']['txHash'],
            response['tx_result']['blockHeight'],
            default_score, to_address, value*0.1, 0.0001,
            response['game_score'])

    result_page = {
        'wallet_address': str(response['wallet_address']),
        'wallet_balance': str(response['wallet_balance']),
        'latest_transaction': str(response['wallet_latest_transaction']),
        'transaction_result': response['transaction_result'],
        'game_score': response['game_score']
    }

    return HttpResponse(str(result_page))
