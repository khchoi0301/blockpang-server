# Enter interactive mode

from iconsdk.icon_service import IconService
from iconsdk.providers.http_provider import HTTPProvider
# icon_service = IconService(HTTPProvider("https://bicon.net.solidwallet.io/api/v3"))
icon_service = IconService(HTTPProvider("http://localhost:9000/api/v3"))
block = icon_service.get_block("latest")
print(block)