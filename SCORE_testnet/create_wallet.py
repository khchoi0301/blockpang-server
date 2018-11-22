# Enter interactive mode
# Create a wallet
from iconsdk.wallet.wallet import KeyWallet
wallet = KeyWallet.create()
# Check the wallet address
# wallet.get_address()
# Let try getting the private key
# wallet.get_private_key()
# Now let's create a keystore
wallet.store('./iconkeystore', '@icon111')
# Let's create another wallet to test transactions later
wallet2 = KeyWallet.create()
wallet2.store('./iconkeystore2', '@icon222')
