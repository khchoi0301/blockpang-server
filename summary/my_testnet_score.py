from iconservice import *

TAG = 'TestnetScore'


class TestnetScore(IconScoreBase):

    _DISPENSE_TRACK = "DISPENSE TRACK"

    @eventlog(indexed=2)
    def FundTransfer(self, backer: Address, amount: int, is_top_up: bool):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._dispenseTracking = DictDB(
            self._DISPENSE_TRACK, db, value_type=int)

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

    # it doesn't work // why?? callBuilder problem???
    @external(readonly=True)
    def get_block(self) -> str:
        return self.get_block('0xee0019ead377d6f9ee560c669f66b6a13811761c2388682d66a0f253cfbcdb24')

    # @external(readonly=True)
    # def get_block(self) -> str:
    #     return str(self.icx.get_block("6934"))
    #     return str(self.icx.get_block("latest"))
    #     return str(self.get_block(6934))
    #     return str(self.icx.get_block(6934))
    #     return self.icx.get_block(6934)
    #     return self.icx.get_block('0xee0019ead377d6f9ee560c669f66b6a13811761c2388682d66a0f253cfbcdb24')

    @external
    def send_icx(self, _to: Address, _from: Address):

        if self._dispenseTracking[_to] > 0 and (self.block.height < self._dispenseTracking[_to] + 5):
            Logger.info(
                f'Please wait for 30 blocks to be created before requesting again', TAG)
            revert('Please wait for 30 blocks to be created before requesting again')

        amount = 5 * 10 ** 17

        result = self.icx.transfer(_to, amount)
        Logger.debug(
            f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)
        self.FundTransfer(_to, amount, False)
        Logger.debug(f'{amount} ICX sent to {_to} ', TAG)
        self._dispenseTracking[_to] = self.block.height
        return result

    @external
    @payable
    def send_icx_p(self, _to: Address, _from: Address):
        amount = 5 * 10 ** 17

        result = self.icx.transfer(_to, amount)
        Logger.debug(
            f'result of self.icx.send for amount {amount} to {_to} is {result}', TAG)
        self.FundTransfer(_to, amount, False)
        Logger.debug(f'{amount} ICX sent to {_to} ', TAG)
        return result

    @payable
    def fallback(self):
        # topup ICX
        Logger.debug(
            f'faucet topup from {self.msg.sender} with amount {self.msg.value}', TAG)
        return 'fallback'
