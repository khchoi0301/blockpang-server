from iconservice import *

TAG = 'DICON'

# The SCORE will take ICX transfers (bets), does a coin flip, winning bets = x1.98

class DiceRoll(IconScoreBase):
    _PLAY_RESULT = "PLAY_RESULT"

    @eventlog(indexed=1)
    def DiceRoll(self, _by: Address, amount: int, result: str):
        pass

    @eventlog(indexed=3)
    def FundTransfer(self, backer: Address, amount: int, is_contribution: bool):
        pass

    def __init__(self, db: IconScoreDatabase) -> None:
        super().__init__(db)
        self._play_results_array = ArrayDB(self._PLAY_RESULT, db, value_type=str)

    def on_install(self) -> None:
        super().on_install()

    def on_update(self) -> None:
        super().on_update()

    # This method is to allow us to topup house balance so we can reward users for winning bets
    @external
    @payable
    def set_treasury(self) -> None:
        Logger.debug(f'{self.msg.value} was added to the treasury from address {self.msg.sender}', TAG)

    # Get house balance
    @external(readonly=True)
    def get_treasury(self) -> int:
        Logger.debug(f'Amount in the treasury is {self.icx.get_balance(self.address)}', TAG)
        return self.icx.get_balance(self.address)

    # All bets received will be passed to this function
    @payable
    def fallback(self):
        amount = self.msg.value

        # Bets must be under 100 ICX
        if amount <= 0 or amount > 100 * 10 ** 18:
            Logger.debug(f'Betting amount {amount} out of range.', TAG)
            revert(f'Betting amount {amount} out of range.')

        # We need at least 2x the betting amount in balance in order to take the bet
        if (self.icx.get_balance(self.address)) < 2 * amount:
            Logger.debug(f'Not enough in treasury to make the play.', TAG)
            revert('Not enough in treasury to make the play.')

        # A simple logic to determine the result, odd numbers = win, even numbers = lose.
        win = int.from_bytes(sha3_256(self.msg.sender.to_bytes() + str(self.block.timestamp).encode()), "big") % 2
        Logger.debug(f'Result of flip was {win}.', TAG)

        json_result = {}
        json_result['index'] = self.tx.index
        json_result['nonce'] = self.tx.nonce
        json_result['from'] = str(self.tx.origin)
        json_result['timestamp'] = self.tx.timestamp
        json_result['txHash'] = bytes.hex(self.tx.hash)
        json_result['amount'] = self.msg.value
        json_result['result'] = win

        self._play_results_array.put(str(json_result))

        # based on result send 1.98x the amount to winner.
        if win == 1:
            payout = int(1.98 * amount)
            Logger.debug(f'Amount owed to winner: {payout}', TAG)

            try:
                self.icx.transfer(self.msg.sender, payout)
                self.FundTransfer(self.msg.sender, payout, False)
                Logger.debug(f'Sent winner ({self.msg.sender}) {payout}.', TAG)
            except:
                Logger.debug(f'Send failed.', TAG)
                revert('Network problem. Winnings not sent. Returning bet.')

        # else keep the amount in the treasury.
        else:
            Logger.debug(f'Player lost. ICX retained in treasury.', TAG)

    # this is for our webapp to query updated results
    @external(readonly=True)
    def get_results(self) -> dict:
        valueArray = []
        for value in  self._play_results_array:
            valueArray.append(value)

        Logger.debug(f'{self.msg.sender} is getting results', TAG)
        return {'result': valueArray}