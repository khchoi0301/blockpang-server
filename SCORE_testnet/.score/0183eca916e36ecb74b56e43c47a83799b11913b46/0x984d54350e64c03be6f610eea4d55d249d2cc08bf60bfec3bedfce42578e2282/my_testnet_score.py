from iconservice import *

TAG = 'TestnetScore'

class TestnetScore(IconScoreBase):

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()
    
    @external(readonly=True)
    def hello(self) -> str:
        Logger.debug(f'Hello, world!', TAG)
        return "Hello123"

    @external(readonly=True)
    def get_balance(self) -> str:
        return self.icx.get_balance(self.address)

    @external(readonly=True)
    def get_address(self) -> str:
        return self.address

    @external(readonly=True)
    def get_params(self, _to:Address, _from: Address) -> str:
        res = 'to:'+ _to + 'from:' +_from
        return res

    @external(readonly=True)
    def get_to(self, _to: Address, _from: Address) -> str:
        return self.icx.get_balance(_to)

    @external(readonly=True)
    def get_from(self, _to: Address, _from: Address) -> str:
        return self.icx.get_balance(_from)

    @external
    def send_icx(self):
        amount = 5 * 10 ** 18
        self.icx.transfer('hxa039d2a3f908ff83de04f8cfe893277eed0c97f0', amount)
        return 'sent'

    @external
    def send_icx2(self):
        amount = 5 * 10 ** 18
        result = self.icx.transfer('hxa039d2a3f908ff83de04f8cfe893277eed0c97f0', amount)
        return result


    @external
    @payable
    def send_icx_p(self, _to: Address, _from: Address):
        amount = 5 * 10 ** 18
        self.icx.transfer(_to, amount)
        Logger.debug('hi',self)
        return 'sent'

    @payable
    def fallback(self):
        #topup ICX
        Logger.debug(f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        return 'fallback'