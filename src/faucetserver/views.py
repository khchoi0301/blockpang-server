from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import connections
from django.core.mail import send_mail
from django.conf import settings
import ast
import os
import time
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


def queryDB(request):
    """DB Query."""
    cursor = connections['default'].cursor()
    cursor.execute("SELECT * FROM transaction")
    query_result = cursor.fetchall()
    return HttpResponse(query_result)


def index(request):
    page = '<div> connet to the uri : faucet/wallet_address/int </div>'
    return HttpResponse(page)


def create_wallet(request):
    return HttpResponse(utils.create_wallet(request))


def set_limit(request, amount_limit, block_limit):
    return HttpResponse(utils.set_limit(request, amount_limit, block_limit))

def get_limit(request):
    limit = utils.get_limit()
    limit['amountlimit'] = int(limit['amountlimit'], 16) / 10 ** 18
    limit['blocklimit'] = int(limit['blocklimit'], 16)
    return HttpResponse(str(limit))


def email(request):
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {request} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['charredbroccoli@gmail.com', 'khchoi0301@gmail.com']
    send_mail(subject, message, email_from, recipient_list)
    print('email has been sent.')
    return HttpResponse('Email sent!')


def show_transaction(request):
    return HttpResponse()


@csrf_exempt  # need to think about security
def req_icx(request, to_address, value):

    wallet_icx_maxlimit = 100 * 10 ** 18
    block_icx_warning_minlimit = 1 * 10 ** 18
    # block_limit = str(block_icx_warning_minlimit)

    value = value

    # email(block_limit)

    if request.method == 'POST':
        print('req', request)
        print('method', request.method)
        req_body = ast.literal_eval(request.body.decode('utf-8'))
        value = req_body['value']
        print('POST VALUE', value)

    response = {}
    response['block_balance'] = int(utils.get_block_balance(), 16)
    response['wallet_balance'] = int(
        utils.get_wallet_balance(request, to_address), 16)

    # send a email to admin when block doesn't have enough icx
    if (response['block_balance'] < block_icx_warning_minlimit):
        # call send_email function
        return HttpResponse('Not enough icx in block - block_icx_warning_minlimit : ' + block_limit)

    # transfer icx only when wallet's balance is under the limit
    if (response['wallet_balance'] > wallet_icx_maxlimit):
        return HttpResponse('You have too much icx in your wallet!!')

    # transfer icx
    response['tx_hash'] = utils.send_transaction(request, to_address, value)

    # check the transaction result
    try:
        time.sleep(6)
        print('6s')
        response['tx_result'] = icon_service.get_transaction_result(
            response['tx_hash'])

    except:
        time.sleep(6)
        print('12s')
        try:
            response['tx_result'] = icon_service.get_transaction_result(
                response['tx_hash'])
        except:
            response['tx_result'] = {'failure': {
                'code': '0x7d65', 'message': "Please wait for few blocks to be created before requesting again"}}

    print(response['tx_result'])

    # check results
    response['block_address'] = default_score
    response['wallet_address'] = to_address
    response['wallet_latest_transaction'] = int(utils.get_latest_transaction(
        request, to_address), 16)
    response['latest_block_height'] = int(utils.get_latest_block_height(), 16)
    response['latest_block_info'] = utils.get_latest_block()
    response['block_balance'] = int(utils.get_block_balance(), 16)
    response['wallet_balance'] = int(
        utils.get_wallet_balance(request, to_address), 16)


    print('1')
    # print('hello',response['tx_result'])
    print(response['tx_result']['txHash'])
    print(response['tx_result']['blockHeight'])
    print(response['tx_result']['stepPrice']/10**18)
    print(response['tx_result']['stepUsed']/10**18)
    
    

    print(response['tx_result']['eventLogs'])
    if response['tx_result']['eventLogs'] is None :
        print(response['tx_result']['failure'])
    else :    
        print(response['tx_result']['eventLogs'][0])
        print(response['tx_result']['eventLogs'][0]['scoreAddress'])
        print(response['tx_result']['eventLogs'][0]['indexed'][2])
        

    print('2')
    
    # INSERT INTO transaction (txhash, block, from_wallet, to_wallet, amount, txfee)
    # (response['tx_result']['txHash'],response['tx_result']['blockHeight'],print(response['tx_result']['eventLogs'][0]['scoreAddress']),print(response['tx_result']['eventLogs'][0]['indexed'][2]),);

    

    page = '<div></div>'+str(response['latest_block_info'])+'<div></div>'+'block height : '+str(response['latest_block_height'])+'<div></div>'+' find_transaction : '+str(response['wallet_latest_transaction'])+'<div>tx_hash : </div>'+response['tx_hash'] + '<div></div>'+'block:' + \
        '<div></div>'+default_score + ' // balance is ' + \
        str(response['block_balance']/10**18) + '<div>to:</div>' + \
        str(to_address)+' // balance is ' + \
        str(response['wallet_balance']/10**18)

    # page = str(response['latest_block_info'])+'<div></div>'+'block height : '+str(response['latest_block_height'])+'<div></div>'+' find_transaction : '+str(response['wallet_latest_transaction'])+'<div>tx_hash : </div>'+response['tx_hash'] + '<div></div>'+'block:' + \
    #     '<div></div>'+default_score + ' // balance is ' + \
    #     str(response['block_balance']/10**18) + '<div>to:</div>' + \
    #     str(to_address)+' // balance is ' + \
    #     str(response['wallet_balance']/10**18)

    return HttpResponse(str(response['tx_result']))

