from django.db import connections
from django.conf import settings
import ast
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
    CallTransactionBuilder,
)
from . import utils_db


cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))
wallet = settings.WALLET
wallet_from = settings.WALLET_FROM


def create_wallet(request):
    new_wallet = {}
    wallet = KeyWallet.create()
    new_wallet['address'] = wallet.get_address()
    new_wallet['key'] = wallet.get_private_key()
    utils_db.insertDB_users(request, new_wallet['address'])
    return new_wallet


def update_wallet(request):
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    try:
        return utils_db.insertDB_users(request, req_body['wallet'])
    except Exception as e:
        return {'status': 'fail', 'Error': str(e)}


def get_wallet_balance(wallet_address):
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_wallet_balance')\
        .params({'_to': wallet_address})\
        .build()
    return int(icon_service.call(call), 16) / 10 ** 18


# Send ICX to wallet
def send_transaction(wallet_address, value):
    print('transaction called', wallet_address, 'value: ', value, type(value))

    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method('send_icx')\
        .params({'_to': wallet_address, 'value': int(value)})\
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    print('transaction complete')

    # Sends the transaction
    return icon_service.send_transaction(signed_transaction)


# Get user wallet's latest transaction
def get_latest_transaction(wallet_address):
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('find_latest_transaction')\
        .params({'_to': wallet_address})\
        .build()
    return int(icon_service.call(call), 16)


def get_latest_block_height():
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('block_height')\
        .build()
    return int(icon_service.call(call), 16)


def get_latest_block():
    return icon_service.get_block('latest')


def get_transaction_result(tx_hash):
    try:
        time.sleep(1)
        print('1s')
        tx_result = icon_service.get_transaction_result(tx_hash)
    except:
        time.sleep(1)
        print('2s')
        try:
            tx_result = icon_service.get_transaction_result(tx_hash)
        except Exception as e:
            return {'status': 'fail', 'Error': str(e)}
    return tx_result


def get_block_balance():
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_balance')\
        .build()
    return int(icon_service.call(call), 16) / 10 ** 18
