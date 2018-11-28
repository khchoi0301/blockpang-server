from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.icon_service import IconService
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.builder.transaction_builder import (
    TransactionBuilder,
    DeployTransactionBuilder,
    CallTransactionBuilder,
    MessageTransactionBuilder
)
from iconsdk.wallet.wallet import KeyWallet

# Load our existing wallet 1
wallet = KeyWallet.load("./iconkeystore", "@icon111")

# Build a transaction instance, hard-code it to send 1 ICX from wallet 1 to wallet 2
transaction = TransactionBuilder()\
    .from_(wallet.get_address())\
    .to("hxc425d7a44a76b17245528ec4225be1e6a2f8635d")\
    .value(1000000000000000000)\
    .step_limit(2000000)\
    .nid(3)\
    .nonce(100)\
    .build()
icon_service = IconService(HTTPProvider(
    "https://bicon.net.solidwallet.io/api/v3"))

# Returns the signed transaction object having a signature
signed_transaction = SignedTransaction(transaction, wallet)

# Sends the transaction
tx_hash = icon_service.send_transaction(signed_transaction)
