# Enter interactive mode
# Get balance through the querying method
from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
balance = icon_service.get_balance('hxb94e8c183b72255057d9d05a28532afa2787682c')/10**18
balance2 = icon_service.get_balance('hx9920fb964da4047c3bd86a6263a62ae2e63e6c96') /10**18
balance3 = icon_service.get_balance('hxc425d7a44a76b17245528ec4225be1e6a2f8635d')/10**18

print(balance)
print(balance2)
print(balance3)
