from iconservice import *

TAG = 'FaucetScore'


class FaucetScore(IconScoreBase):

    _DISPENSE_TRACK = "DISPENSE TRACK"
    _AMOUNT_LIMIT = "AMOUNT LIMIT"
    _BLOCK_LIMIT = "BLOCK LIMIT"

    @eventlog(indexed=2)
    def FundTransfer(self, backer: Address, amount: int, is_top_up: bool):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._dispenseTracking = DictDB(
            self._DISPENSE_TRACK, db, value_type=int)
        self._amountlimit = VarDB(self._AMOUNT_LIMIT, db, value_type=int)
        self._blocklimit = VarDB(self._BLOCK_LIMIT, db, value_type=int)
        # self._amountlimit = 100 * 10 ** 18
        # self._blocklimit = 1
        Logger.info(f'on_init1', TAG)

    def on_install(self, amount: int, block: int) -> None:
        super().on_install()
        amountlimit = amount * 10 ** 18
        self._amountlimit.set(amountlimit)
        self._blocklimit.set(block)
        Logger.info(
            f'on_install1 {self._amountlimit.get()} {self._blocklimit.get()}', TAG)

    def on_update(self, amount: int, block: int) -> None:
        super().on_update()
        amountlimit = amount * 10 ** 18
        self._amountlimit.set(amountlimit)
        self._blocklimit.set(block)
        Logger.info(
            f'on_update {self._amountlimit.get()} {self._blocklimit.get()}', TAG)

    @external(readonly=True)
    def get_balance(self) -> str:
        return self.icx.get_balance(self.address)

    @external(readonly=True)
    def block_height(self) -> str:
        return self.block.height

    @external(readonly=True)
    def find_transaction(self, _to: Address) -> str:
        return self._dispenseTracking[_to]

    @external(readonly=True)
    def get_to(self, _to: Address, _from: Address) -> str:
        return self.icx.get_balance(_to)

    @external
    def set_limit(self, amountlimit: int, blocklimit: int):

        Logger.info(f'this sets amountlimit1', TAG)
        self._amountlimit.set(amountlimit * 10 ** 18)
        self._blocklimit.set(blocklimit)
        Logger.info(
            f'this sets amountlimit2 : {self._amountlimit.get()} ( {self._amountlimit.get()} icx ) blocklimit : {self._blocklimit.get()}', TAG)
        return 'limit changed'

    @external
    def get_limit(self) -> str:
        Logger.info(
            f'thisgetamountlimit1 : {self._amountlimit.get()}  blocklimit : {self._blocklimit.get()}', TAG)
        limit = {}
        limit['amountlimit'] = self._amountlimit.get()
        limit['blocklimit'] = self._blocklimit.get()

        Logger.info(
            f'thisgetamountlimit2 : {self._amountlimit.get()}  blocklimit : {self._blocklimit.get()}', TAG)
        return limit

    @external
    def send_icx(self, _to: Address, value: int):

        # check if the address already asked for in last 30 blocks
        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] + self._blocklimit):
            Logger.info(
                f'Please wait for {self._blocklimit} blocks to be created before requesting again', TAG)
            revert(
                f'Please wait for {self._blocklimit} blocks to be created before requesting again', TAG)

        amount = value * 10 ** 17

        # check if score has enough balance
        if(self.icx.get_balance(self.address) < amount):
            Logger.info(f'Not enough blance in faucet', TAG)
            revert('faucet doesn\'t have balance to dispense')

        if(self._amountlimit < amount):
            Logger.info(f'requested amount is over the limit', TAG)
            revert('requested amount is over the limit')

        result = self.icx.transfer(_to, amount)
        Logger.debug(
            f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)
        self.FundTransfer(_to, amount, False)
        Logger.debug(f'{amount} ICX sent to {_to} ', TAG)
        self._dispenseTracking[_to] = self.block.height
        Logger.info(f'_dispenseTracking{self._dispenseTracking}', TAG)
        return result

    @payable
    def fallback(self):
        # topup ICX
        Logger.debug(
            f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        return 'fallback'
