from django.shortcuts import render
from django.http import HttpResponse
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

default_score = "cx31aef86872e344658372bd23a3cbbc1c810ec8fa"
# icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
icon_service = IconService(HTTPProvider("http://127.0.0.1:9000/api/v3"))


wallet = KeyWallet.load(
    "/home/khchoi/icon-tut/BlockPang/BlockPang/blockpang/faucet-app/keystore_test1.json", "@icon111")
wallet_from = wallet.get_address()
# wallet_from ='hx9920fb964da4047c3bd86a6263a62ae2e63e6c96'
wallet_to = 'hxa039d2a3f908ff83de04f8cfe893277eed0c97f0'


def index(request):

    page = '<div>faucet/wallet_address</div>'
    return HttpResponse(page)
    # return HttpResponse('Bye')


def createwallet(request):

    wallet = KeyWallet.create()
    new_wallet = {}
    # Check the wallet address
    new_wallet['address'] = wallet.get_address()
    # Let try getting the private key
    new_wallet['key'] = wallet.get_private_key()

    return HttpResponse(str(new_wallet))


def setlimit(request, amountlimit, blocklimit):

    limit_setting = {}
    limit_setting['amountlimit'] = amountlimit
    limit_setting['blocklimit'] = blocklimit

    set_limit = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method("set_limit")\
        .params({'amountlimit': amountlimit, 'blocklimit': blocklimit})\
        .build()
    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(set_limit, wallet)
    # Sends the transaction
    tx_hash = str(icon_service.send_transaction(signed_transaction))
    print('set_limit complete', tx_hash)  # added

    return HttpResponse(str(limit_setting))


def req_icx(request, to_address, value):

    wallet_to = to_address
    response = {}
    response['block_address'] = default_score

    # Transfer
    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method("send_icx")\
        .params({'_from': wallet_from, '_to': wallet_to, 'value': value})\
        .build()
    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    # Sends the transaction
    tx_hash = icon_service.send_transaction(signed_transaction)
    print('transaction complete')  # added

    # Balance of the Block
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_balance")\
        .build()
    block_balance = icon_service.call(call)
    response['block_balance'] = block_balance
    print('block_balance', block_balance)

    # Balance of the wallet
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_to")\
        .params({'_from': wallet_from, '_to': wallet_to})\
        .build()
    wallet_balance = icon_service.call(call)
    response['wallet_balance'] = wallet_balance
    print('wallet_balance', wallet_to, wallet_balance)

    # Wallet's latest transaction
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("find_transaction")\
        .params({'_to': wallet_to})\
        .build()
    wallet_latest_transaction = icon_service.call(call)
    response['wallet_latest_transaction'] = wallet_latest_transaction
    print('wallet_latest_transaction', wallet_latest_transaction)

    # Latest block height
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("block_height")\
        .build()
    latest_block_height = icon_service.call(call)
    response['latest_block_height'] = latest_block_height
    print('latest_block_height', latest_block_height)

    # call = CallBuilder().from_(wallet_from)\
    # .to(default_score)\
    # .method("get_block")\
    # .build()
    # get_block = icon_service.call(call)
    # print('get_block',get_block)

    # Latest block info
    latest_block_info = icon_service.get_block('latest')
    response['latest_block_info'] = latest_block_info

    print(latest_block_info)

    page = str(latest_block_info)+'<div></div>'+'block height : '+str(int(latest_block_height, 16))+'<div></div>'+' find_transaction : '+str(int(wallet_latest_transaction, 16))+'<div>tx_hash : </div>'+tx_hash + '<div></div>'+'block:' + \
        '<div></div>'+default_score + ' // block balance' + \
        str(int(block_balance, 16)/10**18) + '<div>to:</div>' + \
        str(wallet_to)+' // balance is ' + str(int(wallet_balance, 16)/10**18)

    return HttpResponse(page)
