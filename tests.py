from . import pages
from otree.api import Currency as c, currency_range
from otree.api import Bot, SubmissionMustFail
from ._builtin import Bot
from otree.api import Submission
from .models import Constants


class PlayerBot(Bot):

    #  Insert cases here
    cases = ['Nash']

    def play_round(self):

        if self.player.id_in_group == 2:
            if self.case == 'Max':
                yield SubmissionMustFail(pages.SellerBidding, {'seller_bid': -25},
                                         check_html=False)
                yield Submission(pages.SellerBidding, {'seller_bid': 60}, check_html=False)
                assert self.group.retention_money == 60
            else:
                yield Submission(pages.SellerBidding, {'seller_bid': 30}, check_html=False)
                assert self.group.retention_money == 30
            yield Submission(pages.AuctionFeedback, timeout_happened=True)
            assert self.player.is_winner == True
            num_winners = sum([1 for p in self.group.get_players() if p.is_winner])
            assert num_winners == 1

        elif self.player.id_in_group == 3:
            if self.case == 'Max':
                yield Submission(pages.SellerBidding, {'seller_bid': 80}, check_html=False)
            else:
                yield Submission(pages.SellerBidding, {'seller_bid': 80}, check_html=False)
            yield Submission(pages.AuctionFeedback, timeout_happened=True)
            assert self.player.is_winner == False
            yield Submission(pages.TriviaQ, timeout_happened=True)
            yield Submission(pages.TriviaAns, timeout_happened=True)

        if self.player.id_in_group == 1:
            if self.case == 'Min':
                yield Submission(pages.BuyerTrade, {'buyer_accept': False}, check_html=False)
            else:
                yield Submission(pages.BuyerTrade, {'buyer_accept': True}, check_html=False)

        if self.case == 'Min' and self.player.is_winner == True:
            yield Submission(pages.TradeFeedback)

        elif self.case == 'Max' and self.player.is_winner == True:
            yield Submission(pages.SellerQuality, {'seller_quality': 1}, check_html=False)

        elif self.case == 'Max' and self.player.id_in_group == 1:
            yield Submission(pages.BuyerTransfer, {'buyer_transfer': 60},
                             check_html=False)

        elif self.case == 'Nash' and self.player.is_winner == True:
            yield Submission(pages.SellerQuality, {'seller_quality': 0})

        elif self.case == 'Nash' and self.player.id_in_group == 1:
            yield Submission(pages.BuyerTransfer, {'buyer_transfer': 0},
                             check_html=False)

        yield (pages.ResultsTreatments)
        if self.case == 'Min':
            assert self.player.payoff == 0
        elif self.case == 'Nash':
            if self.player.is_winner:
                assert self.player.payoff == -30
            elif self.player.role() == 'buyer':
                assert self.player.payoff == 35
            else:
                assert self.player.payoff == 0
        else:
            if self.player.is_winner:
                assert self.player.payoff == 20
            elif self.player.role() == 'buyer':
                assert self.player.payoff == 20
            else:
                assert self.player.payoff == 0
