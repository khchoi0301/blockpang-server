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

        Logger.info(f'on_init', TAG)

    def on_install(self) -> None:
        super().on_install()
        amountlimit = 100 * 10 ** 18
        self._amountlimit.set(amountlimit)
        self._blocklimit.set(30)

        Logger.info(
            f'on_install {self._amountlimit.get()} {self._blocklimit.get()}', TAG)

    def on_update(self) -> None:
        super().on_update()
        amountlimit = 100 * 10 ** 18
        self._amountlimit.set(amountlimit)
        self._blocklimit.set(30)

        Logger.info(
            f'on_update {self._amountlimit.get()} {self._blocklimit.get()}', TAG)

    @external(readonly=True)
    def get_balance(self) -> int:
        Logger.info(f'get_balance {self}', TAG)
        return self.icx.get_balance(self.address)

    @external(readonly=True)
    def get_wallet_balance(self, _to: Address) -> int:
        Logger.info(f'get_balance of {_to}', TAG)
        return self.icx.get_balance(_to)

    @external(readonly=True)
    def block_height(self) -> int:
        Logger.info(f'block_height {self}', TAG)
        return self.block.height

    @external(readonly=True)
    def find_latest_transaction(self, _to: Address) -> int:
        Logger.info(f'find_latest_transaction {self}', TAG)
        return self._dispenseTracking[_to]

    @external
    def set_limit(self, amountlimit: int, blocklimit: int) -> None:

        amountlimit = amountlimit * 10 ** 18
        self._amountlimit.set(amountlimit)
        self._blocklimit.set(blocklimit)

        Logger.info(
            f'Set_limit_called : {self._amountlimit.get()} , {amountlimit} icx ,  blocklimit : {self._blocklimit.get()}', TAG)

    @external(readonly=True)
    def msg_sender(self) -> str:
        Logger.info(f'msg_sender {self} ', TAG)
        Logger.info(f'msg_sender {self.msg.sender}', TAG)

        return self.msg.sender

    @external(readonly=True)
    def getowner(self) -> str:
        Logger.info(f'owner {self}', TAG)
        Logger.info(f'owner {self.owner}', TAG)
        return self.owner

    @external(readonly=True)
    def get_limit(self) -> str:

        limit = {}
        limit['amountlimit'] = self._amountlimit.get()
        limit['blocklimit'] = self._blocklimit.get()

        Logger.info(
            f'Get_limit_called : {self._amountlimit.get()}  blocklimit : {self._blocklimit.get()}', TAG)

        return limit

    @external
    def send_icx(self, _to: Address, value: int) -> str:

        amount = value * 10 ** 16  # need to change 16 to 18 when deploying

        Logger.info(
            f'sendICXcalled {amount} to {_to} value {value} amountlimit : {self._amountlimit.get()} blocklimit : {self._blocklimit.get()}', TAG)

        # check msg came from server
        if self.msg.sender != self.owner:
            Logger.info(
                f'msg sender {self.msg.sender} should be the same as owner {self.owner}', TAG)
            revert(
                f'msg sender {self.msg.sender} should be the same as owner {self.owner}')

        # check the address already asked for in last 30 blocks
        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] + self._blocklimit.get()):
            Logger.info(
                f'Please wait for {self._blocklimit.get()} blocks to be created before requesting again', TAG)
            revert(
                f'Please wait for {self._blocklimit.get()} blocks to be created before requesting again')

        # check score has enough balance
        if(self.icx.get_balance(self.address) < amount):
            Logger.info(f'Not enough blance in faucet', TAG)
            revert('faucet doesn\'t have balance to dispense')

        # check request amount is lower than limit
        if(self._amountlimit.get() < amount):
            Logger.info(f'requested amount is over the limit', TAG)
            revert('requested amount is over the limit')

        result = self.icx.transfer(_to, amount)
        Logger.debug(
            f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)

        self.FundTransfer(_to, amount, False)
        Logger.debug(f'{amount} ICX sent to {_to} ', TAG)

        # record the latest transaction block
        self._dispenseTracking[_to] = self.block.height
        Logger.info(f'_dispenseTracking : {self._dispenseTracking[_to]}', TAG)

        return result

    @payable
    def fallback(self):
        # topup ICX
        Logger.debug(
            f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        return 'fallback'
