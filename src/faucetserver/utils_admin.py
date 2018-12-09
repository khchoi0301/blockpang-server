from django.db import connections
from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db import IntegrityError
import os
import re
import time
import urllib.request
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_200_OK
)
from rest_framework.response import Response
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


# Check admin username and password, and then give token
@api_view(['POST'])
@permission_classes((AllowAny,))
def get_token(request):
    username = request.data.get('username')
    password = request.data.get('password')
    if username is None or password is None:
        return Response(
            {'error': 'Please provide both username and password'},
            status=HTTP_400_BAD_REQUEST)
    user = authenticate(username=username, password=password)
    if not user:
        return Response(
            {'error': 'Invalid Credentials'}, status=HTTP_404_NOT_FOUND)
    token, _ = Token.objects.get_or_create(user=user)
    return Response({'token': 'Token ' + token.key}, status=HTTP_200_OK)


# Get a list of current admins
def get_admins():
    staff_list = []
    staffs = User.objects.filter(is_staff=True).values_list('email', flat=True)
    return staffs[0]


def is_valid_email(email):
    if len(email) > 7:
        return bool(re.match(
            "^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", email))


def email(minlimit):
    recipient = get_admins()
    subject = 'Icon Faucet: Not enough icx'
    message = f'Score has less than {minlimit} icx. Please add icx to score.'
    email_from = settings.EMAIL_HOST_USER
    send_mail(subject, message, email_from, recipient)
    return 'Email has been sent to admins.'


def update_admin(request):
    req_body = utils_db.request_parser(request)
    username = req_body['username']

    try:
        email_address = req_body['email']
        if not is_valid_email(email_address):
            return {
                'admin_email': get_admins(), 
                'message': 'ERROR: Please enter a valid email address'}
    except Exception:
        email_address = None
        # will need to change this if 'add' and 'delete' params return
        return {
            'admin_email': get_admins(),
            'message': 'ERROR: No email address'}

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
                log = f'ERROR: Please provide a different email address'
                return {'admin_email': get_admins(), 'message': log}
            staff.email = email_address
            staff.save()
            log = f'SUCCESS: Email has been updated'
        except Exception as e:
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

    return {'admin_email': get_admins(), 'message': log}


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
    req_body = utils_db.request_parser(request)
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
    time.sleep(1)
    return get_limit()
