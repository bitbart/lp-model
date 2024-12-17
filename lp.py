import math # For math.inf
from math import isclose

# from hypothesis import note, assume, settings
# from hypothesis.strategies import *
from hypothesis.stateful import rule, RuleBasedStateMachine

import logging as log

log.basicConfig(format="%(levelname)s: %(message)s", level=log.DEBUG)

def revert(msg):
    log.info(msg)
    # raise ValueError(msg)
    return

from collections import namedtuple # for Constants
Constants = namedtuple('Constants', ['Cmin'])
LP_constants = Constants(1.5)


class LP(RuleBasedStateMachine):
    """
    A Lending Pool module
    """
    def __init__(self):
        super(LP, self).__init__()
        self.reserves = {}  # reserves map  {token: amount}
        self.debts  = {}    # debts map     {token: {address: amount}}
        self.minted = {}    # minted map    {token: {address: amount}}
        self.prices = {}    # prices map    {token: price}
        self.lastReverted = False

    def pretty_print(self):
        """
        Pretty-prints the internal state of the LP instance on a single line.
        """
        state = {
            "Reserves": self.reserves,
            "Debts": self.debts,
            "Minted": self.minted,
            "Prices": self.prices,
            "LastReverted": self.lastReverted
        }
        print(f"LP: {state}")

    def get_price(self, token):
        if token not in self.prices:
            return 1 # default price
        else:
            return self.prices[token]

    def get_xr(self):
        xr = {tok: self.XR(tok) for tok in self.reserves}
        xr = {tok: xr for tok, xr in xr.items() if xr != 1}
        return xr

    def get_reserves(self, token):
        return self.reserves[token]

    def get_minted(self, token, address):
        if token not in self.minted:
            return 0
        if address not in self.minted[token]:
            return 0
        return self.minted[token][address]

    def get_debts(self, token, address):
        if token not in self.debts:
            return 0
        if address not in self.debts[token]:
            return 0
        return self.debts[token][address]
                
    def tok_supply(self, token):
        if token not in self.minted:
            return 0
        else:
            return sum(self.minted[token].values())

    def tok_debts(self, token):
        return sum(self.debts[token].values())

    def XR(self, token):
        if self.tok_supply(token) == 0:
            return 1
        else:
            return (self.reserves[token] + self.tok_debts(token)) / self.tok_supply(token) 

    def val_minted(self, address):
        val = 0
        for token in self.minted:
            if address in self.minted[token]:
                val += self.minted[token][address] * self.XR(token) * self.get_price(token)
        return val

    def val_debts(self, address):
        val = 0
        for token in self.debts:
            if address in self.debts[token]:
                val += self.debts[token][address] * self.get_price(token)
        return val

    def collateral(self, address):
        if self.val_debts(address) == 0:
            return math.inf # No debts to collateralize (+inf)
        return self.val_minted(address) / self.val_debts(address)

    def is_collateralized(self, address):
        if self.val_debts(address) == 0:
            return True
        return self.collateral(address) >= LP_constants.Cmin

    def set_price(self, token, price):
        """
        Sets the price of a specific token.

        Args:
            token (str): The name or identifier of the token.
            price (float): The price to be set for the token. Must be greater than zero.

        Reverts:
            If the price is less than or equal to zero.

        Side Effects:
            Updates the 'prices' dictionary with the given token and its price.

        Example:
            self.set_price("BTC", 50000)
            # Sets the price of the 'BTC' token to 50000.
        """
        if price <= 0:
            log.info("Price must be greater than zero.")
            self.lastReverted = True
            return
        self.prices[token] = price
        self.lastReverted = False

    def deposit(self, address, amount, token):
        if amount <= 0:
            log.info("Deposit amount must be greater than zero.")
            self.lastReverted = True
            return
        
        # If the address is new, initialize its balance
        if token not in self.reserves:
            self.reserves[token] = amount

            self.debts[token] = {}
            self.debts[token][address] = 0

            self.minted[token] = {}
            self.minted[token][address] = amount / self.XR(token)
        else:
            xr = self.XR(token)
            
            self.reserves[token] += amount
            if address not in self.minted[token]:
                self.debts[token][address] = 0
                self.minted[token][address] = amount / xr
            else:
                self.minted[token][address] += amount / xr

        self.lastReverted = False

    def borrow(self, address, amount, token):
        if amount <= 0:
            log.info("Deposit amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token not in self.reserves:
            log.info("Token not found in reserves.")
            self.lastReverted = True
            return
        elif amount > self.reserves[token]:
            log.info("Insufficient reserves to borrow.")
            self.lastReverted = True
            return
        
        assert(token in self.reserves)

        # Removes amount units of token from the reserves
        self.reserves[token] -= amount

        if token not in self.debts:
            self.debts[token] = {}
        if address not in self.debts[token]:
            self.debts[token][address] = amount
        else:
            self.debts[token][address] += amount

        if self.collateral(address) < LP_constants.Cmin:
            log.info("Address is not collateralized.")
            # reverts the transaction
            self.reserves[token] += amount
            self.debts[token][address] -= amount
            self.lastReverted = True
            return 
        
        self.lastReverted = False

    def repay(self, address, amount, token):
        if amount <= 0:
            log.info("Repay amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token not in self.debts:
            log.info("Token not found in reserves.")
            self.lastReverted = True
            return
        elif address not in self.debts[token]:
            log.info("Address not found in debts.")
            self.lastReverted = True
            return 
        elif amount > self.debts[token][address]:
            log.info("Insufficient debts to repay.")
            self.lastReverted = True
            return 
        
        assert(token in self.reserves)
        assert(token in self.debts)
        assert(address in self.debts[token])

        self.reserves[token] += amount
        self.debts[token][address] -= amount
        self.lastReverted = False

    def interest_rate(self, token):
        return 12/100
    
    def accrue_interest(self):
        for token in self.debts:
            for address in self.debts[token]:
                self.debts[token][address] += self.debts[token][address] * self.interest_rate(token)

    def redeem(self, address, amount, token):
        amount_rdm = amount * self.XR(token)
        log.info(f"{address}: redeem({amount}:{token} minted)")
        log.info(f"redeeming {amount_rdm}:{token}")
        log.info(f"{address} collateral = {self.collateral(address)}")

        if amount <= 0:
            log.info("Redeem amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token not in self.reserves:
            log.info("Token not found in reserves.")
            self.lastReverted = True
            return
        elif address not in self.minted[token]:
            log.info("Address not found in minted.")
            self.lastReverted = True
            return
        elif amount > self.minted[token][address]:
            log.info("Insufficient minted tokens to redeem.")
            self.lastReverted = True
            return
        elif amount_rdm > self.reserves[token]:
            log.info("Insufficient reserves to redeem.")
            self.lastReverted = True
            return
        
        assert(token in self.reserves)
        assert(token in self.minted)
        assert(address in self.minted[token])

        self.reserves[token] -= amount_rdm
        self.minted[token][address] -= amount

        log.info(f"{address} collateral = {self.collateral(address)}")
        if self.collateral(address) < LP_constants.Cmin:
            log.info("Address is not collateralized.")
            # reverts the transaction
            self.reserves[token] += amount_rdm
            self.minted[token][address] += amount
            self.lastReverted = True
            return

        self.lastReverted = False


    # dummy rule to avoid Hypothesis warning
    @rule()
    def dummy(self):
        pass