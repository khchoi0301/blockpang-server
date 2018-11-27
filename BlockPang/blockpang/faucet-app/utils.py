from django.shortcuts import render
from django.http import HttpResponse
import urllib.request
import os
from django.views.decorators.csrf import csrf_exempt

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

# How to call variables from other files

# icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
icon_service = IconService(HTTPProvider("http://127.0.0.1:9000/api/v3"))
default_score = "cxa026915f6c8ae9075b9e8efaafe5776d8cf30956"

keypath = os.path.join(os.path.dirname(__file__), 'iconkeystore')
print('keypath', keypath)
wallet = KeyWallet.load(keypath, "@icon111")
wallet_from = wallet.get_address()


def createwallet(request):

    wallet = KeyWallet.create()
    new_wallet = {}
    # Check the wallet address
    new_wallet['address'] = wallet.get_address()
    # Let try getting the private key
    new_wallet['key'] = wallet.get_private_key()

    return str(new_wallet)

# Set limits


def set_limit(request, amountlimit, blocklimit):

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

    return str(limit_setting)


# Get limits
def get_limit():

    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_limit")\
        .build()
    return icon_service.call(call)

# Balance of the Block


def block_balance():

    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_balance")\
        .build()
    return icon_service.call(call)


# Balance of the wallet
def wallet_balance(request, to_address):

    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_to")\
        .params({'_from': wallet_from, '_to': to_address})\
        .build()
    return icon_service.call(call)


def transaction(request, to_address, value):
    print('transaction called')
    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method("send_icx")\
        .params({'_to': to_address, 'value': value})\
        .build()
    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    print('transaction complete')
    # Sends the transaction
    return icon_service.send_transaction(signed_transaction)


# Wallet's latest transaction
def wallet_latest_transaction(request, to_address):
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("find_transaction")\
        .params({'_to': to_address})\
        .build()
    return icon_service.call(call)


# Latest block height
def latest_block_height():
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("block_height")\
        .build()
    return icon_service.call(call)


# Latest block info
def latest_block_info():
    return icon_service.get_block('latest')
