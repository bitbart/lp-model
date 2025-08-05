import math # For math.inf
from math import isclose
from fractions import Fraction
from string_utils import *

# from hypothesis import note, assume, settings
# from hypothesis.strategies import *
from hypothesis.stateful import rule, RuleBasedStateMachine

import argparse
import sys
import logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

def revert(msg):
    log.info(msg)
    # raise ValueError(msg)
    return

from fractions import Fraction

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
        self.tliq = Fraction(2, 3)  # tliq = liquidation threshold
        self.rliq = Fraction(11,10) # rliq = liquidation reward factor

        # Interest rate parameters: IR(T) = alpha * U(T) + beta
        self.ir_alpha = 0
        self.ir_beta = Fraction(12, 100)  # Default interest rate of 12%

    def pretty_print(self, precise=False):
        """
        Pretty-prints the internal state of the LP instance on a single line.

        Parameters:
        - precise (bool): If True, represent fractions as 'numerator/denominator'.
                          If False, represent fractions as approximate floating-point values.
        """
        state = {
            "Reserves": self.reserves,
            "Debts": self.debts,
            "Minted": self.minted,
            "Prices": self.prices,
            "LastReverted": self.lastReverted
        }
        print(f"{clean_repr(state)}")

    def get_price(self, token):
        if token not in self.prices:
            return Fraction(1) # default price
        else:
            return Fraction(self.prices[token])

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
    
    # supply of minted (credit) tokens
    def tok_supply(self, token):
        if token not in self.minted:
            return 0
        else:
            return sum(self.minted[token].values())

    # supply of debt tokens
    def tok_debts(self, token):
        return sum(self.debts[token].values())

    # exchange rate of minted (credit) token
    def XR(self, token):
        if self.tok_supply(token) == 0:
            return Fraction(1)
        else:
            return Fraction(self.reserves[token] + self.tok_debts(token), self.tok_supply(token)) 

    # net worth of minted (credit) tokens of a given address
    def val_minted(self, address):
        val = Fraction(0)
        for token in self.minted:
            if address in self.minted[token]:
                val += self.minted[token][address] * self.XR(token) * self.get_price(token)
        return val

    # net worth of debt tokens of a given address
    def val_debts(self, address):
        val = Fraction(0)
        for token in self.debts:
            if address in self.debts[token]:
                val += self.debts[token][address] * self.get_price(token)
        return val

    def collateral(self, address):
        if self.val_debts(address) == 0:
            return math.inf # No debts to collateralize (+inf)
        return Fraction(self.val_minted(address), self.val_debts(address))

    def health_factor(self, address):
        if self.val_debts(address) == 0:
            return math.inf # No debts to collateralize (+inf)
        return self.collateral(address) * self.tliq

    def set_liq_threshold(self, tliq):
        log.info(f"set_liq_threshold({tliq})")
        if tliq < 0 or tliq > 1:
            log.warning("Liquidation threshold must be between 0 and 1.")
            self.lastReverted = True
            return
        self.tliq = tliq
        self.lastReverted = False

    def set_liq_reward_factor(self, rliq):
        log.info(f"set_liq_reward_factor({rliq})")
        if rliq < 1:
            log.warning("Liquidation reward factor must be greater than 1.")
            self.lastReverted = True
            return
        self.rliq = rliq
        self.lastReverted = False

    def set_interest_rate(self, alpha, beta):
        log.info(f"set_interest_rate(alpha={alpha},beta={beta})")
        if alpha < 0 or beta < 0:
            log.warning("Interest rate parameters must be greater than 0.")
            self.lastReverted = True
            return
        self.ir_alpha = alpha
        self.ir_beta = beta

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
        log.info(f"set_price({token}, {price})")
        if price <= 0:
            log.warning("Price must be greater than zero.")
            self.lastReverted = True
            return
        self.prices[token] = price
        self.lastReverted = False

    def deposit(self, address, amount, token):
        log.info(f"{address}: deposit({amount}:{token})")

        if amount <= 0:
            log.warning("Deposit amount must be greater than zero.")
            self.lastReverted = True
            return
        
        # If the address is new, initialize its balance
        if token not in self.reserves:
            self.reserves[token] = amount

            self.debts[token] = {}
            self.debts[token][address] = 0

            self.minted[token] = {}
            self.minted[token][address] = Fraction(amount, self.XR(token))
        else:
            xr = self.XR(token)
            
            self.reserves[token] += amount
            if address not in self.minted[token]:
                self.minted[token][address] = Fraction(amount, xr)
            else:
                self.minted[token][address] += Fraction(amount, xr)

        self.lastReverted = False

    def borrow(self, address, amount, token):
        log.info(f"{address}: borrow({amount}:{token})")

        if amount <= 0:
            log.warning("Deposit amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token not in self.reserves:
            log.warning("Token not found in reserves.")
            self.lastReverted = True
            return
        elif amount > self.reserves[token]:
            log.warning("Insufficient reserves to borrow.")
            self.lastReverted = True
            return
        
        assert(token in self.reserves)

        log.info(f"pre:  H({address}) = {float(self.health_factor(address))}")

        # Removes amount units of token from the reserves
        self.reserves[token] -= amount

        if token not in self.debts:
            self.debts[token] = {}
        if address not in self.debts[token]:
            self.debts[token][address] = amount
        else:
            self.debts[token][address] += amount

        log.info(f"post: H({address}) = {float(self.health_factor(address))}")

        if self.health_factor(address) < 1:
            log.warning(f"{address} is not collateralized")
            # reverts the transaction
            self.reserves[token] += amount
            self.debts[token][address] -= amount
            self.lastReverted = True
            return 
        
        self.lastReverted = False
        return amount

    def repay(self, address, amount, token):
        log.info(f"{address}: repay({amount}:{token})")

        if amount <= 0:
            log.warning("Repay amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token not in self.debts:
            log.warning("Token not found in reserves.")
            self.lastReverted = True
            return
        elif address not in self.debts[token]:
            log.warning("Address not found in debts.")
            self.lastReverted = True
            return 
        elif amount > self.debts[token][address]:
            log.warning("Insufficient debts to repay.")
            self.lastReverted = True
            return 
        
        assert(token in self.reserves)
        assert(token in self.debts)
        assert(address in self.debts[token])

        log.info(f"pre:  H({address}) = {float(self.health_factor(address))}")

        self.reserves[token] += amount
        self.debts[token][address] -= amount
        self.lastReverted = False

        log.info(f"post: H({address}) = {float(self.health_factor(address))}")

    def utilization_ratio(self, token):
        """
        Calculates the utilization ratio for a given token T.
        If there are no debts in T, utilization is considered zero.
        """
        if token not in self.reserves or self.tok_debts(token) == 0:
            return Fraction(0)
        return Fraction(self.tok_debts(token), self.reserves[token] + self.tok_debts(token))
        
    def interest_rate(self, token):
        return self.ir_alpha * self.utilization_ratio(token) + self.ir_beta
    
    def accrue_interest(self):
        for token in self.debts:
            log.info(f"accrue_interest on {token}: {self.ir_alpha} * {self.utilization_ratio(token)} + {self.ir_beta} = {self.interest_rate(token)}")
            for address in self.debts[token]:
                self.debts[token][address] += self.debts[token][address] * self.interest_rate(token)

        self.lastReverted = False

    def redeem(self, address, amount, token):
        log.info(f"{address}: redeem({amount}:{token})")

        amount_rdm = amount * self.XR(token)
        log.info(f"XR({token}) = {self.XR(token)}")
        # log.info(f"{address}: redeem({amount}:{token} minted)")
        # log.info(f"redeeming {amount_rdm}:{token}")

        if amount <= 0:
            log.warning("Redeem amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token not in self.reserves:
            log.warning("Token not found in reserves.")
            self.lastReverted = True
            return
        elif address not in self.minted[token]:
            log.warning("Address not found in minted.")
            self.lastReverted = True
            return
        elif amount > self.minted[token][address]:
            log.warning("Insufficient minted tokens to redeem.")
            self.lastReverted = True
            return
        elif amount_rdm > self.reserves[token]:
            log.warning("Insufficient reserves to redeem.")
            self.lastReverted = True
            return
        
        assert(token in self.reserves)
        assert(token in self.minted)
        assert(address in self.minted[token])

        log.info(f"pre:  H({address}) = {float(self.health_factor(address))}")

        self.reserves[token] -= amount_rdm
        self.minted[token][address] -= amount

        log.info(f"post: H({address}) = {float(self.health_factor(address))}")

        if self.health_factor(address) < 1:
            log.warning(f"Address {address} is under-collateralized (collateral = {self.collateral(address)}).")
            # reverts the transaction
            self.reserves[token] += amount_rdm
            self.minted[token][address] += amount
            self.lastReverted = True
            return

        log.info(f"XR({token}) = {self.XR(token)}")

        self.lastReverted = False
        return amount_rdm

    def liquidate(self, address, amount, token_debt, address_debtor, token_minted):
        log.info(f"{address}: liquidate({amount}:{token_debt}, {address_debtor}, {token_minted})")

        amount_minted = Fraction(amount,self.XR(token_minted)) * Fraction(self.get_price(token_debt), self.get_price(token_minted)) * Fraction(self.rliq)

        if amount <= 0:
            log.warning("Liquidate amount must be greater than zero.")
            self.lastReverted = True
            return
        elif token_debt not in self.debts:
            log.warning(f"Token {token_debt} not found in debts.")
            self.lastReverted = True
            return
        elif address_debtor not in self.debts[token_debt]:
            log.warning(f"Address {address_debtor} not found in debts.")
            self.lastReverted = True
            return
        elif amount > self.debts[token_debt][address_debtor]:
            log.warning("Insufficient debts to repay.")
            self.lastReverted = True
            return 
        elif token_minted not in self.minted:
            log.warning(f"Token {token_minted} not found in minted.")
            self.lastReverted = True
            return
        elif address_debtor not in self.minted[token_minted]:
            log.warning(f"Address {address_debtor} not found in minted.")
            self.lastReverted = True
            return
        elif amount_minted > self.minted[token_minted][address_debtor]:
            log.warning("Insufficient minted tokens to redeem.")
            self.lastReverted = True
            return
        elif self.health_factor(address_debtor) >= 1:
            log.warning("Address {address_debtor} is collateralized.")
            self.lastReverted = True
            return
        
        log.info(f"pre:  H({address_debtor}) = {float(self.health_factor(address_debtor))}")

        self.reserves[token_debt] += amount
        self.debts[token_debt][address_debtor] -= amount

        if address not in self.minted[token_minted]:
            self.minted[token_minted][address] = amount_minted
        else:
            self.minted[token_minted][address] += amount_minted

        self.minted[token_minted][address_debtor] -= amount_minted

        log.info(f"post: H({address_debtor}) = {float(self.health_factor(address_debtor))}")

        if self.health_factor(address_debtor) > 1:
            log.warning(f"Address {address_debtor} has health factor > 1")

            # reverts the transaction
            self.reserves[token_debt] -= amount
            self.debts[token_debt][address_debtor] += amount
            self.minted[token_minted][address] -= amount_minted
            self.minted[token_minted][address_debtor] += amount_minted

            self.lastReverted = True
            return
        
        self.lastReverted = False


    # dummy rule to avoid Hypothesis warning
    @rule()
    def dummy(self):
        pass


# Run the main function if the script is executed directly
def main():
    """
    Main function to process a file with transaction commands.
    """
    parser = argparse.ArgumentParser(description="Simulate a Lending Pool from a transaction trace file.")
    parser.add_argument("filename", help="The input file containing transaction trace.")
    parser.add_argument("-p", "--precise", action="store_true",  help="Use precise fraction representation in output.")
    
    args = parser.parse_args()
    is_precise = args.precise

    try:
        with open(args.filename, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"Error: File '{args.filename}' not found.")
        sys.exit(1)
    
    # Create an instance of LP
    lp = LP()

    # Process each line
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        try:
            if line.startswith('#'):
                # Skip comment lines
                continue

            # Example input format: A:deposit(1:T)
            elif ':' in line:
                address, rest = line.split(':', 1)
                if '(' in rest:
                    method, args = rest.split('(', 1)
                    args = args.strip(')')

                    # Parse arguments
                    parsed_args = []
                    for arg in args.split(','):
                        if ':' in arg:  # For example, "1:T"
                            amount, token = arg.split(':')
                            parsed_args.extend([Fraction(amount), token])
                        else:
                            parsed_args.append(arg.strip())

                    # Call the method dynamically
                    if hasattr(lp, method):
                        getattr(lp, method)(address, *parsed_args)
                        lp.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in LP class.")
                else:
                    method = rest
                    if hasattr(lp, method):
                        getattr(lp, method)()
                        lp.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in LP class.")
            else:
                # Non-address-prefixed command, e.g., accrue_interest, set_price(T,2)
                if '(' in line:
                    method, args = line.split('(', 1)
                    args = args.strip(')')
                    parsed_args = []
                    for arg in args.split(','):
                        if arg.replace('.','',1).isdigit(): # arg is a number
                            parsed_args.append(Fraction(arg))
                        else:
                            arg = arg.strip()
                            try:
                                # Try to parse as a Fraction (handles both '2/3' and '3.5')
                                parsed_args.append(Fraction(arg))
                            except ValueError:
                            # Fallback to string or other types if not a valid Fraction
                                parsed_args.append(arg)
                    if hasattr(lp, method):
                        getattr(lp, method)(*parsed_args)
                        lp.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in LP class.")

                else:
                    # No arguments, e.g., accrue_interest
                    method = line
                    if hasattr(lp, method):
                        getattr(lp, method)()
                        lp.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in LP class.")

        except Exception as e:
            log.error(f"Error processing line '{line}': {e}")

# Run the main function if the script is executed directly
if __name__ == "__main__":
    main()