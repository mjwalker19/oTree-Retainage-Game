from otree.api import Currency as c, currency_range
from ._builtin import Page, WaitPage
from .models import Constants
import random

class SellerBidding(Page):
    form_model = 'player'
    form_fields = ['seller_bid', 'seller_exit']

    def is_displayed(self):
        return self.player.role() == 'seller'

    def seller_bid_max(self):
        return self.session.vars['values'][1]

    def seller_bid_min(self):
        return self.session.vars['costs'][0]

    def error_message(self, values):
        if values["seller_exit"] is not True and values["seller_bid"] is None:
            return 'Please enter a bid or exit the round.'

    def vars_for_template(self):
        return self.player.vars_for_template()

class BuyerTrade(Page):
    form_model = 'group'
    form_fields = ['buyer_accept']

    def is_displayed(self):
        if self.player.role() == 'buyer' and not self.group.no_bid:
            return True
        else:
            return False

    def before_next_page(self):
        print('@@@ stage 2 before next page ')
        self.player.show_bid = True
        print('@@@ buyer show price')
        self.player.show_trade = True
        print('@@@ buyer show trade')
        self.player.show_IP = True
        print('@@@ buyer show IP')
        self.group.set_buyer_transfer_default()
        print('@@@ transfer default set')

    def vars_for_template(self):
        return self.player.vars_for_template()

class SellerQuality(Page):
    form_model = 'group'
    form_fields = ['seller_quality']

    def is_displayed(self):
        if self.group.buyer_accept and self.player.is_winner:
            return True
        else:
            return False

    def before_next_page(self):
        print('@@@ stage 3 before next page ')
        self.player.show_trade = True
        print('@@@ winning seller show trade')
        self.player.show_IP = True
        print('@@@ winning seller show IP')
        self.player.show_quality = True
        print('@@@ winning seller show quality')

    def vars_for_template(self):
        return self.player.vars_for_template()

class BuyerTransfer(Page):
    form_model = 'group'
    form_fields = ['buyer_transfer']

    def is_displayed(self):
        if self.session.vars['treatment'] > 0 and self.group.buyer_accept:
            return self.player.role() == 'buyer'
        else:
            return False

    def buyer_transfer_max(self):
        return self.group.retention_money

    def before_next_page(self):
        print('@@@ stage 4 before next page ')
        self.player.show_quality = True
        print('@@@ buyer show quality')
        self.player.show_DP = True
        print('@@@ buyer show DP')

    def vars_for_template(self):
        context = self.player.vars_for_template()
        context.update({'quality': self.group.get_seller_quality_display(),
                        'value': self.session.vars['values'][Constants.qualities.index(self.group.seller_quality)],
                        'cost': self.session.vars['costs'][Constants.qualities.index(self.group.seller_quality)]})
        return context

class SellerAccept(Page):
    form_model = 'group'
    form_fields = ['seller_accept']

    def is_displayed(self):
        if self.session.vars['treatment'] > 2 and self.group.buyer_accept and self.player.is_winner:
            return True
        else:
            return False

    def before_next_page(self):
        print('@@@ stage 5 before next page ')
        self.player.show_DP = True
        print('@@@ winning seller show DP')
        self.player.show_response = True
        print('@@@ winning seller show response')

    def vars_for_template(self):
        context = self.player.vars_for_template()
        context.update({'not_transferred': self.group.retention_money - self.group.buyer_transfer,
                        'BProfitA': self.session.vars['values'][Constants.qualities.index(self.group.seller_quality)] -
                        self.group.initial_payment - self.group.buyer_transfer,
                        'BProfitR': - self.group.initial_payment,
                        'SProfitA': self.group.initial_payment + self.group.buyer_transfer -
                        self.session.vars['costs'][Constants.qualities.index(self.group.seller_quality)],
                        'SProfitR': self.group.initial_payment -
                        self.session.vars['costs'][Constants.qualities.index(self.group.seller_quality)]})
        return context

class ResultsControl(Page):

    timeout_seconds = 25

    def is_displayed(self):
        if self.session.vars['treatment'] == 0:
            return True
        else:
            return False

    def vars_for_template(self):
        context = self.player.vars_for_template()
        if self.group.buyer_accept:
            context.update({'quality': self.group.get_seller_quality_display()})

        return context

class ResultsTreatments(Page):

    timeout_seconds = 25

    def is_displayed(self):
        if self.session.vars['treatment'] > 0:
            return True
        else:
            return False

    def vars_for_template(self):
        context = self.player.vars_for_template()
        if self.group.buyer_accept:
            context.update({'quality': self.group.get_seller_quality_display()})

        return context

class WaitBids(WaitPage):
    template_name = '_game_trust_burden/WaitOther.html'
    wait_for_all_groups = True

    def after_all_players_arrive(self):
        print('@@@ wait bids')
        for player in self.subsession.get_players():
            player.check_exit()
            print('@@@ exit bid set')
        for group in self.subsession.get_groups():
            group.set_winner()
            print('@@@ winner set')
            group.set_retention_money()
            print('@@@ retention money set')
        for player in self.subsession.get_players():
            print('@@@ for player in after_all_players_arrive')
            player.show_bid = True
            print('@@@ all show auction outcome')

    def vars_for_template(self):
        context = self.player.vars_for_template()
        return context

class WaitTrade(WaitPage):
    template_name = '_game_trust_burden/WaitTrade.html'
    wait_for_all_groups = True

    def is_displayed(self):
        if self.player.is_winner:
            return True
        elif self.player.role() == 'buyer' and self.group.no_bid is not True:
            return True
        else:
            return False

    def vars_for_template(self):
        context = self.player.vars_for_template()
        return context

class WaitQuality(WaitPage):
    template_name = '_game_trust_burden/WaitOther.html'
    wait_for_all_groups = True

    def is_displayed(self):
        if self.session.vars['treatment'] > 0:
            if self.player.is_winner and self.group.buyer_accept:
                return True
            elif self.player.role() == 'buyer' and self.group.buyer_accept:
                return True
            else:
                return False
        else:
            return False

    def vars_for_template(self):
        context = self.player.vars_for_template()
        return context

class WaitPayment(WaitPage):
    template_name = '_game_trust_burden/WaitOther.html'
    wait_for_all_groups = True

    def is_displayed(self):
        if self.session.vars['treatment'] > 2:
            if self.player.role() == 'seller' and self.player.is_winner is not False and self.player.seller_exit is not True:
                return True
            elif self.player.role() == 'buyer' and self.group.buyer_accept:
                return True
            else:
                return False
        else:
            return False

    def vars_for_template(self):
        context = self.player.vars_for_template()
        return context

class WaitResult(WaitPage):
    template_name = '_game_trust_burden/WaitResult.html'
    wait_for_all_groups = True

    def after_all_players_arrive(self):
        for group in self.subsession.get_groups():
            print('@@@ for group in after_all_players_arrive')
            group.set_payoffs()
            print('@@@ profit for round set')
            group.set_buyer_transfer_pct()
            print('@@@ transfer pct set')

        for player in self.subsession.get_players():
            print('@@@ for player in after_all_players_arrive')
            player.show_trade = True
            print('@@@ all show bid')
            player.show_IP = True
            print('@@@ all show IP')
            player.show_quality = True
            print('@@@ all show quality')
            player.show_DP = True
            print('@@@ all show DP')
            player.show_response = True
            print('@@@ all show response')
            player.show_payoff = True
            print('@@@ all show payoffs')
            player.cumulative_payoff_set()
            print('@@@ cumulative payoff set')

    def vars_for_template(self):
        context = self.player.vars_for_template()
        return context

page_sequence = [
    SellerBidding,
    WaitBids,
    BuyerTrade,
    WaitTrade,
    SellerQuality,
    WaitQuality,
    BuyerTransfer,
    WaitPayment,
    SellerAccept,
    WaitResult,
    ResultsControl,
    ResultsTreatments,
]
