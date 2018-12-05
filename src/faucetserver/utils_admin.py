from django.db import connections
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
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
    DeployTransactionBuilder,
    CallTransactionBuilder,
    MessageTransactionBuilder
)

cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))


keypath = os.path.join(os.getcwd(), 'keystore_test1')
wallet = KeyWallet.load(keypath, "test1_Account")
wallet_from = wallet.get_address()
print('keypath: ', keypath)


def get_admins():
    staff_list = []
    staffs = User.objects.filter(is_staff=True).values_list('email', flat=True)
    for staff in staffs:
        staff_list.append(staff)
    print(f'List of staffs: {staff_list}')
    return staff_list


def email(minlimit):
    recipient = get_admins()
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {minlimit} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient)
    print('===SUCCESS: email has been sent.===')
    print(recipient)
    return 'Email has been sent to admins.'


def update_admin(request):
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    username = req_body['username']

    if req_body['cmd'] == 'add':
        new_email = req_body['email']
        try:
            print('not in staff list', req_body)
            new_staff = User.objects.create_user(
                username=req_body['username'],
                password=req_body['password'],
                email=new_email
            )
            new_staff.is_superuser = True
            new_staff.is_staff = True
            new_staff.save()
            print(f'===SUCCESS: {new_email} has been added.===')
            log = f'SUCCESS: {new_email} has been added to admin list.'

        except IntegrityError:
            print(f'===ERROR: {new_email} is already in admin list.===')
            log = f'ERROR: {new_email} is already in admin list.'

    elif req_body['cmd'] == 'delete':
        try:
            User.objects.get(
                username=req_body['username'], is_superuser=True).delete()
            print(f'===SUCCESS: {username} has been deleted.===')
            log = f'SUCCESS: {username} has been deleted from admin list.'

        except ObjectDoesNotExist:
            print(f'===ERROR: {username} is not in admin list.===')
            log = f'ERROR: {username} is not in admin list.'

    return {'staff_list': get_admins(), 'logger': log}


def get_limit():
    '''Get limits.'''
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_limit')\
        .build()

    limit = icon_service.call(call)
    limit['amountlimit'] = int(limit['amountlimit'], 16) / 10 ** 18
    limit['blocklimit'] = int(limit['blocklimit'], 16)

    return limit


def set_limit(request):
    '''Set a max amount and frequency of icx Score can send to user.'''
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    amount_limit = req_body['amount_limit']
    block_limit = req_body['block_limit']

    set_limit = CallTransactionBuilder()\
        .from_(wallet.get_address())\
        .to(default_score)\
        .step_limit(5000000)\
        .nid(3)\
        .nonce(100)\
        .method('set_limit')\
        .params({'amountlimit': amount_limit, 'blocklimit': block_limit})\
        .build()

    # Returns the signed transaction object having a signature
    signed_transaction = SignedTransaction(set_limit, wallet)

    # Sends the transaction
    tx_hash = str(icon_service.send_transaction(signed_transaction))
    print('set_limit complete', tx_hash)  # added
    time.sleep(1)
    return get_limit()