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
from iconsdk.signed_transaction import SignedTransaction
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import (
    TransactionBuilder,
    CallTransactionBuilder,
)

cursor = connections['default'].cursor()
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))
wallet = settings.WALLET
wallet_from = settings.WALLET_FROM


# Get a list of current admins
def get_admins():
    staff_list = []
    staffs = User.objects.filter(is_staff=True).values_list('email', flat=True)
    for staff in staffs:
        staff_list.append(staff)
    print(f'Admin: {staff_list}')
    return staff_list


def email(minlimit):
    recipient = get_admins()
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {minlimit} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient)
    print('===SUCCESS: email has been sent.===')
    return 'Email has been sent to admins.'


def update_admin(request):
    req_body = ast.literal_eval(request.body.decode('utf-8'))
    username = req_body['username']

    try:
        email_address = req_body['email']
        if len(email_address) < 1 or '@' not in email_address \
        or '.com' not in email_address:
            print(f'===ERROR: Please enter a valid email address===')
            return {
                'admin': get_admins(), 
                'log': 'ERROR: Please enter a valid email address'}
    except Exception:
        email_address = None
        # will need to change this when 'add' and 'delete' params are back
        print(f'===ERROR: No email address===')
        return {'admin': get_admins(), 'log': 'ERROR: No email address'}

    # -----Add new superuser-----
    # if req_body['cmd'] == 'add':
    #     try:
    #         new_staff = User.objects.create_user(
    #             username=req_body['username'],
    #             password=req_body['password'],
    #             email=email_address
    #         )
    #         new_staff.is_superuser = True
    #         new_staff.is_staff = True
    #         new_staff.save()
    #         print(f'===SUCCESS: {email_address} has been added===')
    #         log = f'SUCCESS: {email_address} has been added to admin list'

    #     except IntegrityError:
    #         print(f'===ERROR: {email_address} is already in admin list===')
    #         log = f'ERROR: {email_address} is already in admin list'
    
    # Edit superuser's email
    if req_body['cmd'] == 'edit':
        try:
            staff = User.objects.get(username=username, is_superuser=True)
            if staff.email == email_address:
                print(f'===ERROR: Please provide a different email address===')
                log = f'ERROR: Please provide a different email address'
                return {'admin': get_admins(), 'log': log}
            staff.email = email_address
            staff.save()
            print(f'===SUCCESS: {email_address} has been updated===')
            log = f'SUCCESS: Email has been updated'
        except Exception as e:
            print(f'===ERROR: {e}===')
            log = str(e)
    
    # -----Delete a superuser-----
    # elif req_body['cmd'] == 'delete':
    #     try:
    #         User.objects.get(
    #             username=req_body['username'], is_superuser=True).delete()
    #         print(f'===SUCCESS: {username} has been deleted===')
    #         log = f'SUCCESS: {username} has been deleted from admin list'

    #     except ObjectDoesNotExist:
    #         print(f'===ERROR: {username} is not in admin list===')
    #         log = f'ERROR: {username} is not in admin list'

    return {'admin': get_admins(), 'log': log}


def get_limit():
    call = CallBuilder().from_(wallet_from)\
        .to(default_score)\
        .method('get_limit')\
        .build()

    limit = icon_service.call(call)
    limit['amountlimit'] = int(limit['amountlimit'], 16) / 10 ** 18
    limit['blocklimit'] = int(limit['blocklimit'], 16)

    return limit


def set_limit(request):
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

    # Send transaction
    tx_hash = str(icon_service.send_transaction(signed_transaction))
    print(f'===set_limit complete: {tx_hash}')
    time.sleep(1)
    return get_limit()
