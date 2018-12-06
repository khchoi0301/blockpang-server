from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.contrib.auth.models import User
from django.db import connections
import ast
import os
import urllib.request
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
from . import utils_admin, utils_db, utils_wallet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


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
    return JsonResponse(utils_db.db_query(table), safe=False)

# Add or delete admin from admin list
@csrf_exempt
def update_admin(request):
    if request.method == 'POST':
        return JsonResponse(utils_admin.update_admin(request), safe=False)


# Create Wallet and Wallet address to USERS DB
@csrf_exempt
def create_wallet(request):
    if request.method == 'POST':
        return JsonResponse(utils_wallet.create_wallet(request))


# Add Wallet address to USERS DB
@csrf_exempt
def update_wallet(request):
    if request.method == 'POST':
        return JsonResponse(utils_wallet.update_wallet(request), safe=False)


# Set MAX ICX transfer limit and MIN block interval limit
@csrf_exempt
def set_limit(request):
    if request.method == 'POST':
        return JsonResponse(utils_admin.set_limit(request))


# Check MAX ICX transfer limit and MIN block interval lilmit
def get_limit(request):
    return JsonResponse(utils_admin.get_limit())


# Transfer ICX to the wallet when conditions are satisfied
@csrf_exempt
def req_icx(request):
    # return Err when request.method is not POST
    if request.method != 'POST':
        return '===ERROR : request.method should be POST'

    # wallet which has more icx than wallet_max_limit can't receive icx
    wallet_max_limit = 100
    # send a email to admin when score has lower icx than score_min_limit
    score_min_limit = 100
    response = {}

    req_body = ast.literal_eval(request.body.decode('utf-8'))
    response['game_score'] = req_body['game_score']
    response['wallet_address'] = req_body['wallet']
    response['block_balance'] = utils_wallet.get_block_balance()
    response['wallet_balance'] = utils_wallet.get_wallet_balance(
        response['wallet_address'])

    # send a email to admin when score doesn't have enough icx
    if response['block_balance'] < score_min_limit:
        utils_admin.email(str(score_min_limit))
        return JsonResponse({
            'status': 'fail',
            'reason': 'Not enough icx in score',
            'log': f'Score has less than {score_min_limit}'
        })

    # transfer icx only when wallet's balance is under the limit
    if response['wallet_balance'] > wallet_max_limit:
        return JsonResponse({
            'status': 'fail',
            'reason': 'Too much icx in wallet',
            'log': f'Wallet has more than {wallet_max_limit}'
        })

    # transfer icx
    response['tx_hash'] = utils_wallet.send_transaction(
        response['wallet_address'], int(response['game_score']))
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
    response['wallet_latest_transaction'] = utils_wallet.get_latest_transaction(
        response['wallet_address'])
    response['latest_block_height'] = utils_wallet.get_latest_block_height()
    response['latest_block_info'] = utils_wallet.get_latest_block()
    response['block_balance'] = utils_wallet.get_block_balance()
    response['wallet_balance'] = utils_wallet.get_wallet_balance(
        response['wallet_address'])

    if not response['tx_result']['eventLogs']:
        print(response['tx_result']['failure'])
    else:
        utils_db.insertDB_transaction(
            response['tx_result']['txHash'],
            response['tx_result']['blockHeight'],
            default_score, response['wallet_address'], int(
                response['game_score']) * 0.01,
            0.0001, response['game_score'])

    result = {
        'wallet_address': str(response['wallet_address']),
        'wallet_balance': str(response['wallet_balance']),
        'latest_transaction': str(response['wallet_latest_transaction']),
        'transaction_result': response['transaction_result'],
        'game_score': response['game_score'],
    }

    if result['transaction_result'] == 'fail':
        err = response['tx_result']['failure']['message']
        result['log'] = err

    return JsonResponse(result)


@csrf_exempt  # need to think about security
def transfer_stat(request):
    return JsonResponse(utils_db.transfer_stat(request), safe=False)
