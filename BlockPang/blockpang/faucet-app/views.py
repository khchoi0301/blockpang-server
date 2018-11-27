import ast
from django.shortcuts import render
from django.http import HttpResponse
import urllib.request
from django.views.decorators.csrf import csrf_exempt
from . import utils
import time
from django.core.mail import send_mail

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


default_score = "cxa026915f6c8ae9075b9e8efaafe5776d8cf30956"
# icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
icon_service = IconService(HTTPProvider("http://127.0.0.1:9000/api/v3"))


def index(request):
    page = '<div> connet to the uri : faucet/wallet_address/int </div>'
    return HttpResponse(page)


def createwallet(request):
    return HttpResponse(utils.createwallet(request))


def setlimit(request, amountlimit, blocklimit):
    return HttpResponse(utils.set_limit(request, amountlimit, blocklimit))


def getlimit(request):
    return HttpResponse(str(utils.get_limit()))


def email(request):
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {request} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['charredbroccoli@gmail.com', 'khchoi0301@gmail.com']
    send_mail(subject, message, email_from, recipient_list)
    print('email has been sent.')
    return HttpResponse('Email sent!')


@csrf_exempt  # need to think about security
def req_icx(request, to_address, value):

    wallet_icx_maxlimit = 100 * 10 ** 18
    block_icx_warning_minlimit = 100 * 10 ** 18
    block_limit = str(block_icx_warning_minlimit)

    value = value

    email(block_limit)

    if request.method == 'POST':
        print('req', request)
        print('method', request.method)
        req_body = ast.literal_eval(request.body.decode('utf-8'))
        value = req_body['value']
        print('POST VALUE', value)

    response = {}
    response['block_balance'] = int(utils.block_balance(), 16)
    response['wallet_balance'] = int(
        utils.wallet_balance(request, to_address), 16)

    # send a email to admin when block doesn't have enough icx
    if (response['block_balance'] < block_icx_warning_minlimit):
        #call send_email function
        return HttpResponse(
            'Not enough icx in block - block_icx_warning_minlimit : ' + block_limit)

    # transfer icx only when wallet's balance is under the limit
    if (response['wallet_balance'] > wallet_icx_maxlimit):
        return HttpResponse('You have too much icx in your wallet!!')

    # transfer icx
    response['tx_hash'] = utils.transaction(request, to_address, value)
    print('call', response['tx_hash'])

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
    response['wallet_latest_transaction'] = int(utils.wallet_latest_transaction(
        request, to_address), 16)
    response['latest_block_height'] = int(utils.latest_block_height(), 16)
    response['latest_block_info'] = utils.latest_block_info()
    response['block_balance'] = int(utils.block_balance(), 16)
    response['wallet_balance'] = int(
        utils.wallet_balance(request, to_address), 16)

    # render info
    page = '<div></div>'+str(response['latest_block_info'])+'<div></div>'+'block height : '+str(response['latest_block_height'])+'<div></div>'+' find_transaction : '+str(response['wallet_latest_transaction'])+'<div>tx_hash : </div>'+response['tx_hash'] + '<div></div>'+'block:' + \
    return HttpResponse(page)
