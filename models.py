from otree.api import (
    models, widgets, BaseConstants, BaseSubsession, BaseGroup, BasePlayer,
    Currency as c, currency_range
)
import random
import csv


author = 'Matthew Walker. Contact at matthew.j.walker@durham.ac.uk'

doc = """
In this game, two sellers compete at a first-price procurement auction to sell one unit of an investment good to a 
randomly matched buyer. If the buyer accepts trade at the winning auction price, the seller chooses a quality level. 
After delivery, the buyer observes the quality level and finalizes payment. <br/>  
<br/> 
Treatments vary according to: <br/> 
(i)	 the proportion of the endogenously determined auction price that is binding for payment; and
(ii) the side of the market that holds residual control rights to the investment good.
 
"""

class Constants(BaseConstants):

    name_in_url = '_2'
    instructions_template = '_intro_trust_burden/SummaryInstructions.html'

    history_table = '_game_trust_burden/HistoryTable.html'

    players_per_group = 3

    num_rounds = 30

    endowment = c(7)  # per round endowment for all players

    outside_option = c(0)
    qualities = [0, 1]

    buyer_transfer_defaults = [0.7, 0.4, 0.6, 0.5, 0.3, 1, 0.8, 0.1, 0.9, 0.2, 0.6, 0, 0.5, 1, 0.1, 0.6, 0.2, 1, 0.7,
                               0.3, 0.4, 0.8, 0.9, 0, 0.5, 0.1, 0.2, 0.7, 0.6, 1]

# for production with >= 3 groups, define the intermingler and shifter functions:
# ctrl-/ for block comment

def intermingler(m):
    for i in m:
        random.shuffle(i)
    b = [[x[1], y[0]] for x, y in zip(m, m[1:] + m[:1])]
    return b

def shifter(m):
    min_group_size = min_group_num = 3
    group_size_err_msg = 'This code will not correctly work for group size not equal {}'.format(min_group_size)
    group_num_err_msg = 'This code will not correctly work if number of groups is less than {}'.format(min_group_num)
    assert Constants.players_per_group == 3, group_size_err_msg
    assert len(m) >= 3, group_num_err_msg
    m = [[i.id_in_subsession for i in l] for l in m]
    f_items = [i[0] for i in m]
    s_items = [i[1:] for i in m]
    s_items = s_items[1:] + [s_items[0]]
    s_items = intermingler(s_items)
    return [[i] + j for i, j in zip(f_items, s_items)]


class Subsession(BaseSubsession):

    # for development can use the following test method to check the matching algorithm functions correctly:
    # def test_previous_matching(self):
    #     if self.round_number > 1:
    #         for p in self.get_players():
    #             otherparts = [i.participant for i in p.get_others_in_group()]
    #             prev_group_parts = [q.participant for q in p.in_round(self.round_number - 1).get_others_in_group()]
    #             if not set(otherparts).isdisjoint(prev_group_parts):
    #                 raise Exception('These players met in the previous round!')

    def creating_session(self):

        # # for development with < 3 groups, use the default random matching protocol:
        # self.group_randomly(fixed_id_in_group=True)
        # self.get_group_matrix()

        # for production with >= 3 groups, use the bespoke algorithm for stranger matching with guaranteed reshuffle:

        if self.round_number > 1:
            prev_matrix = self.in_round(self.round_number - 1).get_group_matrix()
            self.set_group_matrix(shifter(prev_matrix))
        print('MATRIX:: ', self.get_group_matrix())
        # for development with >= 3 groups can add sanity check: self.test_previous_matching()

        if self.round_number == 1:
            for p in self.get_players():
                if p.role() == 'buyer':
                    p.participant.vars['type'] = 1
                    print('@@@ stored in dictionary', p.participant.vars['type'])
                else:
                    p.participant.vars['type'] = 2
                    print('@@@ stored in dictionary', p.participant.vars['type'])

    def vars_for_admin(self):
        sellers = [p for p in self.get_players() if p.role() == 'seller']
        seller_payoffs = [p.payoff for p in sellers]
        seller_cumul_payoffs = [p.cumulative_payoff for p in sellers]
        buyers = [p for p in self.get_players() if p.role() == 'buyer']
        buyer_payoffs = [p.payoff for p in buyers]
        buyer_cumul_payoffs = [p.cumulative_payoff for p in buyers]

        return {'treatment': self.session.vars['treatment'],
                'retention': self.session.vars['retention'],
                'cost_low': self.session.vars['costs'][0],
                'cost_high': self.session.vars['costs'][1],
                'value_low': self.session.vars['values'][0],
                'value_high': self.session.vars['values'][1],
                'avg_buyer_payoff': sum(buyer_payoffs) / len(buyer_payoffs),
                'avg_seller_payoff': sum(seller_payoffs) / len(seller_payoffs),
                'min_buyer_payoff': min(buyer_payoffs),
                'max_buyer_payoff': max(buyer_payoffs),
                'min_seller_payoff': min(seller_payoffs),
                'max_seller_payoff': max(seller_payoffs),
                'avg_buyer_cumul_payoff': sum(buyer_cumul_payoffs) / len(buyer_cumul_payoffs),
                'avg_seller_cumul_payoff': sum(seller_cumul_payoffs) / len(seller_cumul_payoffs),
                'min_seller_cumul_payoff': min(seller_cumul_payoffs),
                'max_seller_cumul_payoff': max(seller_cumul_payoffs),
                'min_buyer_cumul_payoff': min(buyer_cumul_payoffs),
                'max_buyer_cumul_payoff': max(buyer_cumul_payoffs),
                'avg_bid': '',
                'avg_buyer_trade': '',
                'avg_seller_quality': '',
                'avg_buyer_transfer': '',
                'avg_seller_accept': ''
                }

    def vars_for_admin_report(self):
        # Each round is a subsession
        seller_bids = [p.seller_bid for p in self.get_players() if p.seller_bid != None and p.seller_bid != 999]
        buyer_accepts = [g.buyer_accept for g in self.get_groups() if g.buyer_accept != None]
        seller_qualities = [g.seller_quality for g in self.get_groups() if g.seller_quality != None]
        buyer_transfers = [g.buyer_transfer_pct for g in self.get_groups() if g.buyer_transfer_pct != None]
        seller_accepts = [g.seller_accept for g in self.get_groups() if g.seller_accept != None]

        context = self.vars_for_admin()
        if buyer_accepts and self.session.vars['treatment'] == 0:
            if seller_qualities:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                'avg_buyer_trade': (sum(buyer_accepts) / len(buyer_accepts))*100,
                                'avg_seller_quality': (sum(seller_qualities) / len(seller_qualities))*100
                                })
            else:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                'avg_buyer_trade': (sum(buyer_accepts) / len(buyer_accepts))*100
                                })
            return context

        elif buyer_accepts and (self.session.vars['treatment'] == 1 or self.session.vars['treatment'] == 1.5 or self.session.vars['treatment'] == 2):
            if buyer_transfers:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                'avg_buyer_trade': (sum(buyer_accepts) / len(buyer_accepts))*100,
                                'avg_seller_quality': (sum(seller_qualities) / len(seller_qualities))*100,
                                'avg_buyer_transfer': (sum(buyer_transfers) / len(buyer_transfers))*100
                                })
            else:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                'avg_buyer_trade': (sum(buyer_accepts) / len(buyer_accepts))*100,
                                })
            return context

        elif buyer_accepts and self.session.vars['treatment'] > 2:
            if seller_accepts:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                'avg_buyer_trade': (sum(buyer_accepts) / len(buyer_accepts))*100,
                                'avg_seller_quality': (sum(seller_qualities) / len(seller_qualities))*100,
                                'avg_buyer_transfer': (sum(buyer_transfers) / len(buyer_transfers))*100,
                                'avg_seller_accept': (sum(seller_accepts) / len(seller_accepts))*100
                                })
            else:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                'avg_buyer_trade': (sum(buyer_accepts) / len(buyer_accepts))*100
                                })
            return context

        elif seller_bids:
                context.update({'avg_bid': sum(seller_bids) / len(seller_bids),
                                })
        return context


class Group(BaseGroup):
    winning_bid = models.FloatField()
    losing_bid = models.FloatField()
    bids_submitted = models.IntegerField()
    retention_money = models.FloatField()
    initial_payment = models.FloatField()
    buyer_transfer_pct = models.FloatField()
    buyer_payoff = models.CurrencyField()
    seller_payoff = models.CurrencyField()

    no_bid = models.BooleanField(doc="""True if both sellers exit at auction""")

    buyer_accept = models.BooleanField(
        doc="""Whether buyer accepts trade at winning auction price""",
        choices=[
            (True, 'Yes'),
            (False, 'No'),
        ])

    seller_quality = models.IntegerField(
        doc="""Seller quality level delivered""",
        choices=[
            (0, 'Low'),
            (1, 'High')
        ])

    buyer_transfer = models.FloatField(
    min=0, doc="""Amount of retention money the buyer transfers to the seller as deferred payment""",
    widget=widgets.Slider(attrs={'step': '0.25'}))

    seller_accept = models.BooleanField(
        doc="""Whether seller agrees or disputes retention payment decision""",
        choices=[
            (True, 'Accept'),
            (False, 'Reject'),
        ])

    def set_winner(self):
        bidders = self.get_players()
        bids = sorted([p.seller_bid for p in bidders if p.role() == 'seller'])
        self.winning_bid = bids[0]
        self.losing_bid = bids[1]
        if self.winning_bid == 999:
            self.no_bid = True
            self.bids_submitted = 0
            print('@@@ num bids', self.bids_submitted)
        else:
            players_with_winning_bid = [
                p for p in bidders
                if p.seller_bid == self.winning_bid
                ]
            # if tie, winner is chosen at random
            winner = random.choice(players_with_winning_bid)
            winner.is_winner = True
            other = self.get_other_seller()
            for p in other:
                p.is_winner = False
            for p in bidders:
                print('@@@ winner?', p.is_winner)
            if self.losing_bid == 999:
                self.bids_submitted = 1
                print('@@@ num bids', self.bids_submitted)
            else:
                self.bids_submitted = 2
                print('@@@ num bids', self.bids_submitted)

    def set_retention_money(self):
        if self.no_bid is not True:
            self.retention_money = self.session.vars['retention'] * self.winning_bid
            print('@@@ ret money', self.retention_money)
            self.initial_payment = (1 - self.session.vars['retention']) * self.winning_bid
            print('@@@ initial', self.initial_payment)
        else:
            self.retention_money = 0

    def set_buyer_transfer_default(self):
        if self.session.vars['retention'] > 0 and self.buyer_accept is True:
            self.buyer_transfer = self.retention_money*Constants.buyer_transfer_defaults[self.round_number - 1]
            print('@@@ transfer default set')

    def set_buyer_transfer_pct(self):
        if self.session.vars['retention'] > 0 and self.buyer_accept is True:
            self.buyer_transfer_pct = self.buyer_transfer/self.retention_money

    def get_cost(self):
        cost = self.session.vars['costs'][Constants.qualities.index(self.seller_quality)]
        print('@@@ cost', cost)
        return cost

    def get_value(self):
        if self.seller_accept is not False:
            val = self.session.vars['values'][Constants.qualities.index(self.seller_quality)]
            print('@@@ val a', val)
            return val
        else:
            val = 0
            print('@@@ val b', val)
            return val

    def get_payment(self):
        if self.session.vars['retention'] == 0:
            payment = self.initial_payment
            print('@@@ payment a', payment)
            return payment
        elif self.session.vars['retention'] > 0 and self.seller_accept is not False:
            payment = self.initial_payment + self.buyer_transfer
            print('@@@ payment b', payment)
            return payment
        else:
            payment = self.initial_payment
            print('@@@ payment c', payment)
            return payment

    def get_winning_seller(self):
        winner = [p for p in self.get_players() if p.role() == 'seller' and p.is_winner]
        return winner

    def get_other_seller(self):
        other = [p for p in self.get_players() if p.role() == 'seller' and not p.is_winner]
        return other

    def set_payoffs(self):  # profit per round
        buyer = self.get_player_by_role('buyer')
        print('@@@ buyer', buyer)
        winning_seller = self.get_winning_seller()
        print('@@@ winning seller', winning_seller)
        other_seller = self.get_other_seller()
        print('@@@ other seller', other_seller)

        if self.buyer_accept:
            buyer.payoff = self.get_value() - self.get_payment()
            self.buyer_payoff = buyer.payoff
            for p in winning_seller:
                p.payoff = self.get_payment() - self.get_cost()
                self.seller_payoff = p.payoff
            for p in other_seller:
                p.payoff = Constants.outside_option

        else:
            for p in self.get_players():
                p.payoff = Constants.outside_option
            self.buyer_payoff = Constants.outside_option
            self.seller_payoff = Constants.outside_option

class Player(BasePlayer):

    seller_bid = models.IntegerField(
        doc="""Seller bid at auction; set as 999 if seller exits""", blank=True,
    )

    seller_exit = models.BooleanField(
        doc="""Seller exit at auction""", blank=True,
    )

    is_winner = models.BooleanField(
        doc="""Indicates whether the player is the auction winner""",
    )

    accumulated_points = models.CurrencyField(
        doc="""Participant's accumulated points with endowment no limited liability""",
        initial=0,
    )

    cumulative_payoff = models.CurrencyField(
        doc="""Participant's cumulative payoff with limited liability up to that point - so only correct after final period""",
        initial=0,
    )

    show_bid = models.BooleanField(initial=False)
    show_trade = models.BooleanField(initial=False)
    show_IP = models.BooleanField(initial=False)
    show_quality = models.BooleanField(initial=False)
    show_DP = models.BooleanField(initial=False)
    show_response = models.BooleanField(initial=False)
    show_payoff = models.BooleanField(initial=False)

    def role(self):
        if self.id_in_group == 1:
            return 'buyer'
        else:
            return 'seller'

    def cumulative_payoff_set(self):  # total payoff across all rounds
        self.accumulated_points += sum([p.payoff for p in self.in_all_rounds()]) + Constants.endowment*self.round_number
        self.cumulative_payoff += sum([p.payoff for p in self.in_all_rounds()]) + Constants.endowment*self.round_number
        print('@@@ stored in database', self.cumulative_payoff)
        if self.cumulative_payoff < 0:
            self.cumulative_payoff = 0  # limited liability
            print('@@@ limited liability check', self.cumulative_payoff)
        self.participant.vars['payoff'] = self.cumulative_payoff
        print('@@@ stored in dictionary', self.participant.vars['payoff'])
        self.participant.payoff = self.participant.vars['payoff']
        print('@@@ stored in session', self.participant.payoff)

    def check_exit(self):
        if self.seller_exit is True:
            self.seller_bid = 999

    def vars_for_template(self):
        history = self.in_all_rounds()
        history = reversed(history)

        return {'treatment': self.session.vars['treatment'],
                'player_in_all_rounds': history,
                'cost_low': self.session.vars['costs'][0],
                'cost_high': self.session.vars['costs'][1],
                'value_low': self.session.vars['values'][0],
                'value_high': self.session.vars['values'][1]
                }
