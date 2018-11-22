from iconservice import *
import json

TAG = 'TestnetScore'

class TestnetScore(IconScoreBase):

    _DISPENSE_TRACK = "DISPENSE TRACK"
    
    @eventlog(indexed=2)
    def FundTransfer(self, backer: Address, amount: int, is_top_up: bool):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._dispenseTracking = DictDB(self._DISPENSE_TRACK, db, value_type=int)

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


    # it doesn't work // why?? callBuilder problem???
    @external(readonly=True)   
    def get_block(self) -> str:
        return str(icx.get_block("latest"))
        
    @external(readonly=True)   
    def block_height(self) -> str:
        return self.block.height

    @external(readonly=True)
    def get_info(self) -> str:
        return str(self._dispenseTracking)


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
    def send_icx(self, _to: Address, _from: Address):

        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] +30):
            Logger.info(f'Please wait for 30 blocks to be created before requesting again', TAG)
            revert('Please wait for 30 blocks to be created before requesting again')

        amount = 5 * 10 ** 17

        result = self.icx.transfer(_to, amount)
        Logger.debug(f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)
        self.FundTransfer(_to, amount, False)
        Logger.debug(f'{amount} ICX sent to {_to} ', TAG)
        return result


    @external
    @payable
    def send_icx_p(self, _to: Address, _from: Address):
        amount = 5 * 10 ** 17

        result = self.icx.transfer(_to, amount)
        Logger.debug(f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)
        self.FundTransfer(_to, amount, False)
        Logger.debug(f'{amount} ICX sent to {_to} ', TAG)
        return result

    @payable
    def fallback(self):
        #topup ICX
        Logger.debug(f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        return 'fallback'