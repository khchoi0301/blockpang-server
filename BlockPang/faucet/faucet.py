from iconservice import *

TAG = 'Faucet'


class Faucet(IconScoreBase):
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
    def get_balance(self) -> int:
        return self.icx.get_balance(self.address)

    @external
    def send_icx(self, _to: Address):
        if self.msg.sender != self.owner:
            Logger.info(f'Only owner are allowed to call send_icx', TAG)
            revert('Invalid sender: not owner')

        Logger.info(f'self.block.height {self.block.height} and self._dispenseTracking[_to] {self._dispenseTracking[_to]} ' )
        # check if the address already asked for in last 30 blocks
        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] +30):
            Logger.info(f'Please wait for 30 blocks to be created before requesting again', TAG)
            revert('Please wait for 30 blocks to be created before requesting again')

        amount = 20 * 10 ** 18

        # check if score has enough balance
        if(self.icx.get_balance(self.address) < amount):
            Logger.info(f'Not enough blance in faucet', TAG)
            revert('faucet doesn\'t have balance to dispense')

        #send 1 icx
        try:
            result = self.icx.transfer(_to, amount)
            Logger.debug(f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)
            self.FundTransfer(_to, amount, False)
            Logger.debug(f'{amount} ICX sent to {_to} ', TAG)
            self._dispenseTracking[_to] = self.block.height
        except:
            Logger.debug(f'send result is {result} due to bug so might have sent ', TAG)
            revert(f'Failed to send ICX sent to {_to}')

        return result
    @payable
    def fallback(self):
        #topup ICX
        Logger.debug(f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        self.FundTransfer(self.msg.sender, self.msg.value, True)
