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

# def test(request):
#   return HttpResponse('test')


def req_icx(request, to_address):

    wallet_to = to_address

    # Transfer
    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method("send_icx")\
        .params({'_from': wallet_from, '_to': wallet_to})\
        .build()
    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    # Sends the transaction
    tx_hash = icon_service.send_transaction(signed_transaction)
    print('transaction complete')  # added

    # Address of the Block
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_address")\
        .build()
    get_address = icon_service.call(call)
    print('get_address', get_address)

    # Balance of the Block
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_balance")\
        .build()
    get_balance = icon_service.call(call)
    print('get_balance', get_balance)

    # Balance of to_Address
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_to")\
        .params({'_from': wallet_from, '_to': wallet_to})\
        .build()
    get_to = icon_service.call(call)
    print('get_to', wallet_to, get_to)

    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("find_transaction")\
        .params({'_to': wallet_to})\
        .build()
    find_transaction = icon_service.call(call)
    print('find_transaction', find_transaction)

    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("block_height")\
        .build()
    block_height = icon_service.call(call)
    print('block_height', block_height)

    # call = CallBuilder().from_(wallet_from)\
    # .to(default_score)\
    # .method("get_block")\
    # .build()
    # get_block = icon_service.call(call)
    # print('get_block',get_block)

    page = 'block height : '+str(int(block_height, 16))+'<div></div>'+' find_transaction : '+str(int(find_transaction, 16))+'<div>tx_hash : </div>'+tx_hash + '<div></div>'+'block:' + \
        '<div></div>'+get_address + ' // block balance' + \
        str(int(get_balance, 16)/10**18) + '<div>to:</div>' + \
        str(wallet_to)+' // balance is ' + str(int(get_to, 16)/10**18)
    return HttpResponse(page)
