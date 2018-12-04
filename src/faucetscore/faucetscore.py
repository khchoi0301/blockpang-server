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

        Logger.info(f'on_init', TAG)

    def on_install(self) -> None:
        super().on_install()
        amountlimit = 100 * 10 ** 18
        self._amountlimit = amountlimit
        self._blocklimit = 30

        Logger.info(
            f'on_install {self._amountlimit} {self._blocklimit}', TAG)

    def on_update(self) -> None:
        super().on_update()
        amountlimit = 100 * 10 ** 18
        self._amountlimit = amountlimit
        self._blocklimit = 30

        Logger.info(
            f'on_update {self._amountlimit} {self._blocklimit}', TAG)

    @external(readonly=True)
    def get_balance(self) -> str:
        Logger.info(f'get_balance {self}', TAG)
        return self.icx.get_balance(self.address)

    @external(readonly=True)
    def get_wallet_balance(self, _to: Address) -> str:
        Logger.info(f'get_balance of {_to}', TAG)
        return self.icx.get_balance(_to)

    @external(readonly=True)
    def block_height(self) -> str:
        Logger.info(f'block_height {self}', TAG)
        return self.block.height

    @external(readonly=True)
    def find_latest_transaction(self, _to: Address) -> str:
        Logger.info(f'find_latest_transaction {self}', TAG)
        return self._dispenseTracking[_to]

    @external
    def set_limit(self, amountlimit: int, blocklimit: int):

        self._amountlimit = amountlimit * 10 ** 18
        self._blocklimit = blocklimit

        Logger.info(
            f'Set_limit_called : {self._amountlimit} , {amountlimit} icx ,  blocklimit : {self._blocklimit}', TAG)

        return 'limit changed'

    @external
    def get_limit(self) -> str:

        limit = {}
        limit['amountlimit'] = self._amountlimit
        limit['blocklimit'] = self._blocklimit

        Logger.info(
            f'Get_limit_called : {self._amountlimit}  blocklimit : {self._blocklimit}', TAG)

        return limit

    @external
    def send_icx(self, _to: Address, value: int):

        amount = value * 10 ** 17

        Logger.info(
            f'sendICXcalled {amount} to {_to} value {value} amountlimit : {self._amountlimit} blocklimit : {self._blocklimit}', TAG)

        # check if the address already asked for in last 30 blocks
        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] + self._blocklimit):
            Logger.info(
                f'Please wait for {self._blocklimit} blocks to be created before requesting again', TAG)
            revert(
                f'Please wait for {self._blocklimit} blocks to be created before requesting again')

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
        Logger.info(f'_dispenseTracking : {self._dispenseTracking[_to]}', TAG)

        return result

    @payable
    def fallback(self):
        # topup ICX
        Logger.debug(
            f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        return 'fallback'
