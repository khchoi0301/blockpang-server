from iconservice import *

TAG = 'TestnetScore'


class TestnetScore(IconScoreBase):

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

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    @external(readonly=True)
    def hello(self) -> str:
        Logger.debug(f'Hello, world!', TAG)
        return "Hello"

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
    def get_address(self) -> str:
        return self.address

    @external(readonly=True)
    def get_to(self, _to: Address, _from: Address) -> str:
        return self.icx.get_balance(_to)

    # @external(readonly=True)
    # def get_txresult(self, tx_hash: str) -> str:
    #     Logger.info(
    #         f'get_txresult of {tx_hash} ', TAG)
    #     return self.icx.get_transaction_result(tx_hash)

    # @external(readonly=True) # it doesn't work // why?? callBuilder problem???
    # def get_block(self) -> str:
    #     return self.get_block('0xee0019ead377d6f9ee560c669f66b6a13811761c2388682d66a0f253cfbcdb24')

    @external
    def set_limit(self, amountlimit: int, blocklimit: int):
        self._amountlimit = amountlimit * 10 ** 18
        self._blocklimit = blocklimit
        Logger.info(
            f'this sets amountlimit : {self._amountlimit} ( {amountlimit} icx ) blocklimit : {self._blocklimit}', TAG)
        return 'limit changed'

    @external
    def send_icx(self, _to: Address, value: int):

        # check if the address already asked for in last 30 blocks
        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] + self._blocklimit):
            Logger.info(
                f'Please wait for {self._blocklimit} blocks to be created before requesting again', TAG)
            revert(
                f'Please wait for {self._blocklimit} blocks to be created before requesting again', TAG)

        amount = 5 * 10 ** 17 * value

        # check if score has enough balance
        if(self.icx.get_balance(self.address) < amount * 100):
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
