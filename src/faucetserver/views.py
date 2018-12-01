from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import connections
import ast
import datetime
import json
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
from . import utils

 
default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))


def index(request):
    staff_list = []
    staffs = User.objects.filter(is_staff=True).values_list('email', flat=True)
    for staff in staffs:
        staff_list.append(staff)
    print(staff_list)
    return JsonResponse({'admin_email': staff_list})


@staff_member_required
def db_query(request, table):
    return JsonResponse(utils.db_query(request, table), safe=False)


@csrf_exempt
def update_admin(request):
    if request.method == 'POST':
        return JsonResponse(utils.update_admin(request), safe=False)


@staff_member_required
def get_current_balance(request):
    return JsonResponse({
        'default_score': default_score, 
        'current_balance': utils.get_block_balance()
    })


def get_highest_gscores(request):
    data = utils.get_highest_gscores(request)
    return JsonResponse(data, safe=False)


@csrf_exempt  # need to think about security
def create_wallet(request):
    if request.method == 'POST':
        return JsonResponse(utils.create_wallet(request))


@csrf_exempt  # need to think about security
def update_wallet(request):
    if request.method == 'POST':
        return JsonResponse(utils.update_wallet(request), safe=False)


@staff_member_required
@csrf_exempt  # need to think about security
def transfer_stat(request):
    return JsonResponse(utils.transfer_stat(request), safe=False)


@staff_member_required
@csrf_exempt  # need to think about security
def user_stat(request):
    return JsonResponse(utils.user_stat(request))


@staff_member_required
def set_limit(request, amount_limit, block_limit):
    return JsonResponse(utils.set_limit(request, amount_limit, block_limit))


@staff_member_required
def get_limit(request):
    limit = utils.get_limit()
    limit['amountlimit'] = int(limit['amountlimit'], 16) / 10 ** 18
    limit['blocklimit'] = int(limit['blocklimit'], 16)
    return JsonResponse(limit)


@csrf_exempt  # need to think about security
def req_icx(request):

    response = {}

    wallet_max_limit = 100 * 10 ** 18
    score_min_limit = 10 * 10 ** 18
    value = 0.1

    # Update game score
    if request.method == 'POST':
        req_body = ast.literal_eval(request.body.decode('utf-8'))
        response['game_score'] = req_body['game_score']
        to_address = req_body['wallet']
        value = int(response['game_score'])

    response['block_balance'] = int(utils.get_block_balance(), 16)
    response['wallet_balance'] = int(
        utils.get_wallet_balance(request, to_address), 16)

    # transfer icx
    response['tx_hash'] = utils.send_transaction(request, to_address, value)

    # Add transaction_result key to result
    response['tx_result'] = utils.get_transaction_result(response['tx_hash'])
    if (int(response['tx_result']['status']) == 0):
        response['transaction_result'] = 'fail'
    else:
        response['transaction_result'] = 'success'

    # send a email to admin when score doesn't have enough icx
    if (response['block_balance'] < score_min_limit):
        utils.email(str(score_min_limit))
        return JsonResponse({
            'status': 'fail',
            'reason': 'Not enough icx in score',
            'error_log': f'Score has less than {score_min_limit}'
            })

    # transfer icx only when wallet's balance is under the limit
    if (response['wallet_balance'] > wallet_max_limit):
        return JsonResponse({
            'status': 'fail',
            'reason': 'Too much icx in wallet',
            'error_log': f'Wallet has more than {wallet_max_limit}'
        })

    # Check result
    response['block_address'] = default_score
    response['wallet_address'] = to_address
    response['wallet_latest_transaction'] = int(utils.get_latest_transaction(
        request, to_address), 16)
    response['latest_block_height'] = int(utils.get_latest_block_height(), 16)
    response['latest_block_info'] = utils.get_latest_block()
    response['block_balance'] = int(utils.get_block_balance(), 16)
    response['wallet_balance'] = int(
        utils.get_wallet_balance(request, to_address), 16)

    if not response['tx_result']['eventLogs']:
        print(response['tx_result']['failure'])
    else:
        utils.insertDB_transaction(
            response['tx_result']['txHash'],
            response['tx_result']['blockHeight'],
            default_score, to_address, value*0.1, 0.0001,
            response['game_score'])

    result = {
        'wallet_address': str(response['wallet_address']),
        'wallet_balance': str(response['wallet_balance']),
        'latest_transaction': str(response['wallet_latest_transaction']),
        'transaction_result': response['transaction_result'],
        'game_score': response['game_score'],
    }

    if result['transaction_result'] == 'fail':
        err = response['tx_result']['failure']['message']
        err = err[23:]
        result['error_log'] = err

    return JsonResponse(result)
