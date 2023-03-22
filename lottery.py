import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self):
        # storage
        self.init(
            players = sp.map(l = {}, tkey = sp.TNat, tvalue = sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(5),
            max_tickets = sp.nat(5),
            operator = sp.test_account("admin").address
        )

    @sp.entry_point
    def buy_ticket(self, tickets_to_buy):
        sp.set_type(tickets_to_buy, sp.TNat)
        
        # assertions
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(self.data.tickets_available >= tickets_to_buy, "NOT ENOUGH TICKETS LEFT TO DISPENSE")
        sp.verify(sp.amount >= sp.mul(tickets_to_buy, self.data.ticket_cost), "AMOUNT NOT ENOUGH")
        sp.verify(sp.amount >= sp.tez(1), "INVALID AMOUNT")

        # storage changes
        self.data.players[sp.len(self.data.players)] = sp.sender
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - tickets_to_buy)

        # return extra tez
        extra_amount = sp.amount - sp.mul(tickets_to_buy, self.data.ticket_cost)
        sp.if extra_amount > sp.tez(0):
            sp.send(sp.sender, extra_amount)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)
        
        # assertion
        sp.verify(self.data.tickets_available == 0, "GAME IS STILL ON")
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORISED")
        
        # generate a winning index
        winner_index = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_index]

        # send reward to the winner
        sp.send(winner_address, sp.balance)

        # reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets

    @sp.entry_point
    def change_ticket_cost(self, new_cost):
        sp.set_type(new_cost, sp.TNat)

        # assertion
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "A GAME IS ON")
        sp.verify(new_cost > 0, "FREE TICKETS NOT ALLOWED")

        # update ticket cost
        self.data.ticket_cost = sp.utils.nat_to_tez(new_cost)

    @sp.entry_point
    def change_max_tickets(self, new_max):
        sp.set_type(new_max, sp.TNat)

        # assertion
        sp.verify(sp.sender == self.data.operator, "NOT AUTHORISED")
        sp.verify(self.data.tickets_available == self.data.max_tickets, "A GAME IS ON")

        # update max number of available tickets
        self.data.max_tickets  = new_max

        # update number of available tickets
        self.data.tickets_available = new_max
    
    @sp.add_test(name = "main")
    def test():
        scenario = sp.test_scenario()

        # Test accounts
        admin = sp.test_account("admin")
        alice = sp.test_account("alice")
        bob = sp.test_account("bob")
        john = sp.test_account("john")
        mike = sp.test_account("mike")
        charles = sp.test_account("charles")

        # Contract instance
        lottery = Lottery()
        scenario += lottery

        # buy_ticket
        scenario += lottery.buy_ticket(1).run(
            amount = sp.tez(1),
            sender = alice
        )

        scenario += lottery.buy_ticket(2).run(
            amount = sp.tez(2),
            sender = bob
        )

        scenario += lottery.buy_ticket(2).run(
            amount = sp.tez(1),
            sender = mike,
            valid = False
        )

        scenario += lottery.buy_ticket(2).run(
            amount = sp.tez(5),
            sender = john
        )

        scenario += lottery.buy_ticket(1).run(
            amount = sp.tez(1),
            sender = charles,
            valid = False
        )

        # end_game
        scenario += lottery.end_game(25).run(now = sp.timestamp(5), sender = admin)

        # change_ticket_cost
        scenario += lottery.change_ticket_cost(5).run(now = sp.timestamp(5), sender = admin)

        # change_max_tickets
        scenario += lottery.change_max_tickets(20).run(now = sp.timestamp(5), sender = admin)

        # buy_ticket pt. 2
        scenario += lottery.buy_ticket(1).run(
            amount = sp.tez(5),
            sender = alice
        )

        scenario += lottery.buy_ticket(10).run(
            amount = sp.tez(100),
            sender = bob
        )

        # change_ticket_cost (while GAME IS ON)
        scenario += lottery.change_ticket_cost(10).run(now = sp.timestamp(5), sender = admin, valid = False)

        # change_max_tickets (while GAME IS ON)
        scenario += lottery.change_max_tickets(40).run(now = sp.timestamp(5), sender = admin, valid = False)
