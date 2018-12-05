# from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core import serializers
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.db import connections
import ast
import os
import urllib.request
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from iconsdk.builder.call_builder import CallBuilder
from iconsdk.builder.transaction_builder import (
    TransactionBuilder,
    DeployTransactionBuilder,
    CallTransactionBuilder,
    MessageTransactionBuilder
)
from . import utils, utils_admin, utils_db, utils_wallet


default_score = settings.DEFAULT_SCORE_ADDRESS
icon_service = IconService(HTTPProvider(settings.ICON_SERVICE_PROVIDER))


def index(request):
    staff_list = []
    staffs = User.objects.filter(is_staff=True).values_list('email', flat=True)
    for staff in staffs:
        staff_list.append(staff)
    print(staff_list)
    return JsonResponse({'admin_email': staff_list})


@csrf_exempt
def db_query(request, table):
    return JsonResponse(utils_db.db_query(request, table), safe=False)


@csrf_exempt
def update_admin(request):
    if request.method == 'POST':
        return JsonResponse(utils_admin.update_admin(request), safe=False)


def get_highest_gscores(request):
    return JsonResponse(utils_db.get_highest_gscores(request), safe=False)


@csrf_exempt  # need to think about security
def create_wallet(request):
    if request.method == 'POST':
        return JsonResponse(utils_wallet.create_wallet(request))


@csrf_exempt  # need to think about security
def update_wallet(request):
    if request.method == 'POST':
        return JsonResponse(utils_wallet.update_wallet(request), safe=False)


@csrf_exempt
def set_limit(request):
    if request.method == 'POST':
        return JsonResponse(utils_admin.set_limit(request))


def get_limit(request):
    return JsonResponse(utils_admin.get_limit())


@csrf_exempt  # need to think about security
def req_icx(request):
    response = {}
    wallet_max_limit = 100
    score_min_limit = 10
    value = 1

    # Update game score
    if request.method == 'POST':
        req_body = ast.literal_eval(request.body.decode('utf-8'))
        response['game_score'] = req_body['game_score']
        to_address = req_body['wallet']
        value = int(response['game_score'])

    response['block_balance'] = utils_wallet.get_block_balance()
    response['wallet_balance'] = utils_wallet.get_wallet_balance(
        request, to_address)

    # send a email to admin when score doesn't have enough icx
    if (response['block_balance'] < score_min_limit):
        utils_admin.email(str(score_min_limit))
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

    # transfer icx
    response['tx_hash'] = utils_wallet.send_transaction(
        request, to_address, value)
    print('tx_hash', response['tx_hash'])

    # Add transaction_result key to result
    response['tx_result'] = utils_wallet.get_transaction_result(
        response['tx_hash'])
    if (int(response['tx_result']['status']) == 0):
        response['transaction_result'] = 'fail'
    else:
        response['transaction_result'] = 'success'

    # Check result
    response['block_address'] = default_score
    response['wallet_address'] = to_address
    response['wallet_latest_transaction'] = utils_wallet.get_latest_transaction(
        request, to_address)
    response['latest_block_height'] = utils_wallet.get_latest_block_height()
    response['latest_block_info'] = utils_wallet.get_latest_block()
    response['block_balance'] = utils_wallet.get_block_balance()
    response['wallet_balance'] = utils_wallet.get_wallet_balance(
        request, to_address)

    if not response['tx_result']['eventLogs']:
        print(response['tx_result']['failure'])
    else:
        utils.insertDB_transaction(
            response['tx_result']['txHash'],
            response['tx_result']['blockHeight'],
            default_score, to_address, value*0.01, 0.0001,
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
        result['error_log'] = err

    return JsonResponse(result)


@csrf_exempt  # need to think about security
def transfer_stat(request):
    return JsonResponse(utils_db.transfer_stat(request), safe=False)
