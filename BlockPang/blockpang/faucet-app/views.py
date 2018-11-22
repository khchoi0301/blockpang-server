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


default_score = "cx2656a557af0316076ed488f24d3a0d7e3b4c69e5"
icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
# icon_service = IconService(HTTPProvider("http://127.0.0.1:9000/api/v3"))


wallet = KeyWallet.load("/home/khchoi/icon-tut/BlockPang/BlockPang/blockpang/faucet-app/keystore_test1.json", "@icon111")
wallet_from = wallet.get_address()
# wallet_from ='hx9920fb964da4047c3bd86a6263a62ae2e63e6c96'
wallet_to ='hxa039d2a3f908ff83de04f8cfe893277eed0c97f0'


def index(request):

    # Start from calling a string
    # call = CallBuilder().from_(wallet_from)\
    # .to(default_score)\
    # .method("hello")\
    # .build()
    # hello = icon_service.call(call)
    # print('hello',hello)

    # Address of the Block
    call = CallBuilder().from_(wallet_from)\
    .to(default_score)\
    .method("get_address")\
    .build()
    get_address = icon_service.call(call)
    print('get_address',get_address)

    # Balance of the Block
    call = CallBuilder().from_(wallet_from)\
    .to(default_score)\
    .method("get_balance")\
    .build()
    get_balance = icon_service.call(call)
    print('get_balance',get_balance)

    # Balance of to Address
    call = CallBuilder().from_(wallet_from)\
    .to(default_score)\
    .method("get_to")\
    .params({'_from':wallet_from,'_to':wallet_to})\
    .build()
    get_to = icon_service.call(call)
    print('get_to',wallet_to,get_to)

    # Balance of from Address
    call = CallBuilder().from_(wallet_from)\
    .to(default_score)\
    .method("get_from")\
    .params({'_from':wallet_from,'_to':wallet_to})\
    .build()
    get_from = icon_service.call(call)
    print('get_from',wallet_from,get_from)

    # call = CallBuilder().from_(wallet_from)\
    # .to(default_score)\
    # .method("send_icx")\
    # .build()
    # send_icx = icon_service.call(call)
    # print('send_icx',send_icx)


    # Transfer
    print('transaction called')
    params = {}
    transaction = TransactionBuilder()\
    .from_(wallet.get_address())\
    .to(wallet_to)\
    .value(500000000000000000)\
    .step_limit(2000000)\
    .nid(3)\
    .nonce(100)\
    .build()
    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    # Sends the transaction
    tx_hash = icon_service.send_transaction(signed_transaction)
    print('transaction complete')  # added

    
    page = '<div>from:</div>'+ str(wallet_from)+' // balance is '+ str(int(get_from,16)/10**18)     +'<div>to:</div>'+ str(wallet_to)+' // balance is '+ str(int(get_to,16)/10**18) + '<div></div>'+'block:'+'<div></div>'+get_address +'block balance'+ get_balance
    return HttpResponse(page)
    # return HttpResponse('Bye')

def test(request):
  return HttpResponse('test')



  