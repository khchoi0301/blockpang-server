from django.db import connections
from django.conf import settings
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

keypath = os.path.join(os.getcwd(), 'keystore_test1')
wallet = KeyWallet.load(keypath, "test1_Account")
wallet_from = wallet.get_address()
print('keypath: ', keypath)


def create_wallet(request):
    new_wallet = {}
    wallet = KeyWallet.create()
    new_wallet['address'] = wallet.get_address()
    new_wallet['key'] = wallet.get_private_key()
    utils_db.insertDB_users(request, new_wallet['address'])
    return new_wallet


def update_wallet(request):
    try:
        return utils_db.insertDB_users(request, 'include wallet address')
    except Exception as e:
        return {'status': 'fail', 'error_log': str(e)}


def get_wallet_balance(to_address):
    '''Get a wallet balance.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_wallet_balance')\
        .params({'_to': to_address})\
        .build()
    return int(icon_service.call(call), 16) / 10 ** 18


def send_transaction(to_address, value):
    '''Send icx to a wallet.'''
    print('transaction called', to_address, 'value : ', value, type(value))

    transaction = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method('send_icx')\
        .params({'_to': to_address, 'value': int(value)})\
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(transaction, wallet)
    print('transaction complete')

    # Sends the transaction
    return icon_service.send_transaction(signed_transaction)


def get_latest_transaction(to_address):
    '''Get a wallet's latest transaction.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('find_latest_transaction')\
        .params({'_to': to_address})\
        .build()
    return int(icon_service.call(call), 16)


def get_latest_block_height():
    '''Get the latest block's height.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('block_height')\
        .build()
    return int(icon_service.call(call), 16)


def get_latest_block():
    '''Get the latest block.'''
    return icon_service.get_block('latest')


def get_transaction_result(tx_hash):
    # check the transaction result
    try:
        time.sleep(6)
        print('6s')
        tx_result = icon_service.get_transaction_result(tx_hash)

    except:
        time.sleep(6)
        print('12s')
        try:
            tx_result = icon_service.get_transaction_result(tx_hash)
        except:
            tx_result = {'failure': {
                'code': '0x7d65',
                'message': "Please wait for few blocks to be created \
                before requesting again"}}

    return tx_result


def get_block_balance():
    '''Get a block's balance.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_balance')\
        .build()
    return int(icon_service.call(call), 16) / 10 ** 18
