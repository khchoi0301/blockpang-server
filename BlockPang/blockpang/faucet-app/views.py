import ast
from django.shortcuts import render
from django.http import HttpResponse
import urllib.request
import os
from django.views.decorators.csrf import csrf_exempt
from . import utils

from django.core.mail import send_mail
from django.conf import settings

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
# keypath = os.path.join(os.path.dirname(__file__), 'iconkeystore')
# print('keypath', keypath)
# wallet = KeyWallet.load(keypath, "@icon111")
# wallet_from = wallet.get_address()


def index(request):
    page = '<div> connet to the uri : faucet/wallet_address/int </div>'
    return HttpResponse(page)


def createwallet(request):
    return HttpResponse(utils.createwallet(request))


def setlimit(request, amountlimit, blocklimit):
    return HttpResponse(utils.setlimit(request, amountlimit, blocklimit))


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
    response['block_address'] = default_score
    response['block_balance'] = int(utils.block_balance(), 16)
    response['wallet_address'] = to_address
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

    # check results
    response['wallet_latest_transaction'] = int(utils.wallet_latest_transaction(
        request, to_address), 16)
    response['latest_block_height'] = int(utils.latest_block_height(), 16)
    response['latest_block_info'] = utils.latest_block_info()

    # check transaction records
    # i = 3000
    # arr = []
    # while i < 3110:
    #     item = icon_service.get_block(i)
    #     if (item['confirmed_transaction_list'] and item['confirmed_transaction_list'][0] and item['confirmed_transaction_list'][0]['data']):
    #         arr.append(
    #             (item['confirmed_transaction_list'][0]['data']))
    #     i = i + 1

    # print('arr')

    # call = CallBuilder().from_(wallet_from)\
    # .to(default_score)\
    # .method("get_block")\
    # .build()
    # get_block = icon_service.call(call)
    # print('get_block',get_block)

    # email(block_limit)

    page = str(response['latest_block_info'])+'<div></div>'+'block height : '+str(response['latest_block_height'])+'<div></div>'+' find_transaction : '+str(response['wallet_latest_transaction'])+'<div>tx_hash : </div>'+response['tx_hash'] + '<div></div>'+'block:' + \
        '<div></div>'+default_score + ' // balance is ' + \
        str(response['block_balance']/10**18) + '<div>to:</div>' + \
        str(to_address)+' // balance is ' + \
        str(response['wallet_balance']/10**18)

    return HttpResponse(page)


# @csrf_exempt  # need to think about sequrity
# def req_icx(request, to_address, value):

#     value = value

#     if request.method == 'POST':
#         print('req', request)
#         print('method', request.method)
#         req_body = ast.literal_eval(request.body.decode('utf-8'))
#         value = req_body['value']
#         print('POST VALUE', value)

#     wallet_icx_maxlimit = 100 * 10 ** 18
#     block_icx_warning_minlimit = 100 * 10 ** 18

#     response = {}
#     response['block_address'] = default_score

#     # Balance of the Block
#     call = CallBuilder().from_(wallet_from)\
#         .to(default_score)\
#         .method("get_balance")\
#         .build()
#     block_balance = icon_service.call(call)
#     response['block_balance'] = block_balance
#     print('block_balance', block_balance)

#     # Balance of the wallet
#     call = CallBuilder().from_(wallet_from)\
#         .to(default_score)\
#         .method("get_to")\
#         .params({'_from': wallet_from, '_to': to_address})\
#         .build()
#     wallet_balance = icon_service.call(call)
#     response['wallet_balance'] = wallet_balance
#     print('wallet_balance', to_address,
#           wallet_balance, int(response['wallet_balance'], 16))

#     # send a email to admin when block doesn't have enough icx
#     if (int(response['block_balance'], 16) < block_icx_warning_minlimit):
#         return HttpResponse('Block doesnt have enough icx - block_icx_warning_minlimit : '+str(block_icx_warning_minlimit))

#     # transfer icx when wallet's balance is under the limit
#     if (int(response['wallet_balance'], 16) < wallet_icx_maxlimit):
#         print('transaction called', int(response['wallet_balance'], 16))
#         transaction = CallTransactionBuilder()\
#             .from_(wallet.get_address())\
#             .to(default_score)\
#             .step_limit(5000000)\
#             .nid(3)\
#             .nonce(100)\
#             .method("send_icx")\
#             .params({'_from': wallet_from, '_to': to_address, 'value': value})\
#             .build()
#         # Returns the signed transaction object having a signature
#         signed_transaction = SignedTransaction(transaction, wallet)
#         # Sends the transaction
#         tx_hash = icon_service.send_transaction(signed_transaction)
#         print('transaction complete')  # added
#     else:
#         return HttpResponse('You have too much icx to get more!!')

#     # Wallet's latest transaction
#     call = CallBuilder().from_(wallet_from)\
#         .to(default_score)\
#         .method("find_transaction")\
#         .params({'_to': to_address})\
#         .build()
#     wallet_latest_transaction = icon_service.call(call)
#     response['wallet_latest_transaction'] = wallet_latest_transaction
#     print('wallet_latest_transaction', wallet_latest_transaction)

#     # Latest block height
#     call = CallBuilder().from_(wallet_from)\
#         .to(default_score)\
#         .method("block_height")\
#         .build()
#     latest_block_height = icon_service.call(call)
#     response['latest_block_height'] = latest_block_height
#     print('latest_block_height', latest_block_height)

#     # Latest block info
#     latest_block_info = icon_service.get_block('latest')
#     response['latest_block_info'] = latest_block_info
#     # print(latest_block_info)

#     # call = CallBuilder().from_(wallet_from)\
#     # .to(default_score)\
#     # .method("get_block")\
#     # .build()
#     # get_block = icon_service.call(call)
#     # print('get_block',get_block)

#     page = str(latest_block_info)+'<div></div>'+'block height : '+str(int(latest_block_height, 16))+'<div></div>'+' find_transaction : '+str(int(wallet_latest_transaction, 16))+'<div>tx_hash : </div>'+tx_hash + '<div></div>'+'block:' + \
#         '<div></div>'+default_score + ' // balance is ' + \
#         str(int(block_balance, 16)/10**18) + '<div>to:</div>' + \
#         str(to_address)+' // balance is ' + str(int(wallet_balance, 16)/10**18)

#     return HttpResponse(page)
