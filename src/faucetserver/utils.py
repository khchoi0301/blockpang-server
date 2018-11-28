from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
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

# icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
icon_service = IconService(HTTPProvider("http://127.0.0.1:9000/api/v3"))

default_score = "cxa026915f6c8ae9075b9e8efaafe5776d8cf30956"

# keypath = os.path.join(os.path.dirname(__file__), 'iconkeystore')
# print('keypath', keypath)
# wallet = KeyWallet.load(keypath, "@icon111")
# wallet_from = wallet.get_address()


def create_wallet(request):
    """Create a wallet."""
    wallet = KeyWallet.create()
    new_wallet = {}
    # Check the wallet address
    new_wallet['address'] = wallet.get_address()
    # Let try getting the private key
    new_wallet['key'] = wallet.get_private_key()

    return str(new_wallet)


def set_limit(request, amount_limit, block_limit):
    """Set a max amount and frequency of icx Score can send to user."""
    limit_setting = {}
    limit_setting['amount_limit'] = amount_limit
    limit_setting['block_limit'] = block_limit

    set_limit = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method("set_limit")\
        .params({'amount_limit': amount_limit, 'block_limit': block_limit})\
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(set_limit, wallet)

    # Sends the transaction
    tx_hash = str(icon_service.send_transaction(signed_transaction))
    print('set_limit complete', tx_hash)  # added

    return str(limit_setting)


def get_block_balance():
    """Get a block's balance."""
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_balance")\
        .build()

    return icon_service.call(call)


def get_wallet_balance(request, to_address):
    """Get a wallet balance."""
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("get_to")\
        .params({'_from': wallet_from, '_to': to_address})\
        .build()
    return icon_service.call(call)


def send_transaction(request, to_address, value):
    """Send icx to a wallet."""
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


def get_latest_transaction(request, to_address):
    """Get a wallet's latest transaction."""
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("find_transaction")\
        .params({'_to': to_address})\
        .build()
    return icon_service.call(call)


def get_latest_block_height():
    """Get the latest block's height."""
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method("block_height")\
        .build()
    return icon_service.call(call)


def get_latest_block():
    """Get the latest block."""
    return icon_service.get_block('latest')
