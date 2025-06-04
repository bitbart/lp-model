from lp import LP
from string_utils import *
import argparse
import sys
import logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)

class Blockchain:

    def __init__(self):
        self.lp = LP()
        self.wallets = {}  # wallet map  {token: {address: amount}}
        self.lastReverted = False

    def pretty_print(self, precise=False):
        """
        Pretty-prints the internal state of a blockchain instance on a single line.

        Parameters:
        - precise (bool): If True, represent fractions as 'numerator/denominator'.
                          If False, represent fractions as approximate floating-point values.
        """
        print(f"{clean_repr(self.wallets)} | ", end='')
        self.lp.pretty_print(precise)

    # Mint tokens to an address
    def faucet(self, address, amount, token):
        log.info(f"{address}: faucet({amount}:{token})")

        # if amount <= 0:
        #     log.warning("Faucet amount must be greater than zero.")
        #     self.lastReverted = True
        #     return

        if token not in self.wallets:
            self.wallets[token] = {}
        if address not in self.wallets[token]:
            self.wallets[token][address] = 0
    
        self.wallets[token][address] += amount
        self.lastReverted = False

    def get_tokens(self, address, token):
        if token not in self.wallets:
            return 0
        if address not in self.wallets[token]:
            return 0
        return self.wallets[token][address]

    def __set_tokens(self, address, token, amount):
        if token not in self.wallets:
            self.wallets[token] = {}
        self.wallets[token][address] = amount

    def net_worth(self, address):
        """
        Returns the net worth of an address in terms of all tokens.
        """
        net_worth = 0

        # Value of tokens in address' wallet
        for token, balance in self.wallets.items():
            if address in balance:
                net_worth += balance[address] * self.lp.get_price(token)

        # Value of tokens in credit tokens
        for token, balance in self.lp.minted.items():
            if address in balance:
                net_worth += balance[address] * self.lp.XR(token) * self.lp.get_price(token)

        # Value of tokens in debit tokens
        for token, balance in self.lp.debts.items():
            if address in balance:
                net_worth -= balance[address] * self.lp.get_price(token)

        return net_worth
    
    # Method wrappers for the LP model

    def set_liq_threshold(self, tliq):
        self.lp.set_liq_threshold(tliq)
        if self.lp.lastReverted:
            log.warning("set_liq_threshold failed.")
            self.lastReverted = True
            return

    def set_liq_reward_factor(self, rliq):
        self.lp.set_liq_reward_factor(rliq)
        if self.lp.lastReverted:
            log.warning("set_liq_reward_factor failed.")
            self.lastReverted = True
            return

    def deposit(self, address, amount, token):
        if amount <= 0:
            log.warning("Deposit amount must be greater than zero.")
            self.lastReverted = True
            return
        
        a_tok = self.get_tokens(address,token)
        
        if a_tok<amount:
            log.warning(f"Address {address} has insufficient units of {token}")
            self.lastReverted = True
            return
        
        self.lp.deposit(address, amount, token)

        if self.lp.lastReverted:
            log.warning(f"Deposit failed for {address} with {amount}:{token}")
            self.lastReverted = True
            return
        self.__set_tokens(address, token, a_tok - amount)

    def borrow(self, address, amount, token):
        if amount <= 0:
            log.warning("Borrow amount must be greater than zero.")
            self.lastReverted = True
            return

        a_tok = self.get_tokens(address,token)

        out_tok = self.lp.borrow(address, amount, token)

        if self.lp.lastReverted:
            log.warning(f"Borrow failed for {address} with {amount}:{token}")
            self.lastReverted = True
            return
        
        # if lp.borrow does not revert, then it must return the amount of token borrowed
        assert(out_tok == amount)

        # updates the address' wallet
        self.__set_tokens(address, token, a_tok + out_tok)

    def repay(self, address, amount, token):
        if amount <= 0:
            log.warning("Repay amount must be greater than zero.")
            self.lastReverted = True
            return
        
        a_tok = self.get_tokens(address,token)

        if a_tok<amount:
            log.warning(f"Address {address} has insufficient units of {token}")
            self.lastReverted = True
            return
        
        self.lp.repay(address, amount, token)

        if self.lp.lastReverted:
            log.warning(f"Repay failed for {address} with {amount}:{token}")
            self.lastReverted = True
            return
        self.__set_tokens(address, token, a_tok - amount)

    def accrue_interest(self):
        self.lp.accrue_interest()
        if self.lp.lastReverted:
            log.warning("accrue_interest failed.")
            self.lastReverted = True
            return
        
    def set_price(self, token, price):
        self.lp.set_price(token, price)
        if self.lp.lastReverted:
            log.warning("set_price failed.")
            self.lastReverted = True
            return

    def redeem(self, address, amount, token):
        if amount <= 0:
            log.warning("Borrow amount must be greater than zero.")
            self.lastReverted = True
            return

        a_tok = self.get_tokens(address,token)

        out_tok = self.lp.redeem(address, amount, token)

        if self.lp.lastReverted:
            log.warning(f"Redeem failed for {address} with {amount}:{token}")
            self.lastReverted = True
            return
        
        # if lp.redeem does not revert, then it must return the amount of token redeemed
        assert(out_tok >= amount)

        # updates the address' wallet
        self.__set_tokens(address, token, a_tok + out_tok)

    def liquidate(self, address, amount, token_debt, address_debtor, token_minted):
        if amount <= 0:
            log.warning("Liquidate amount must be greater than zero.")
            self.lastReverted = True
            return
        
        a_tok = self.get_tokens(address,token_debt)
        
        if a_tok<amount:
            log.warning(f"Address {address} has insufficient units of {token_debt}")
            self.lastReverted = True
            return
        
        self.lp.liquidate(address, amount, token_debt, address_debtor, token_minted)

        if self.lp.lastReverted:
            log.warning(f"Liquidate failed for {address} with {amount}:{token_debt}")
            self.lastReverted = True
            return
        
        self.__set_tokens(address, token_debt, a_tok - amount)


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
    
    # Create an instance of Blockchain
    bc = Blockchain()

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
                            parsed_args.extend([int(amount), token])
                        else:
                            parsed_args.append(arg.strip())

                    # Call the method dynamically
                    if hasattr(bc, method):
                        getattr(bc, method)(address, *parsed_args)
                        bc.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in Blockchain class.")
                else:
                    method = rest
                    if hasattr(bc, method):
                        getattr(bc, method)()
                        bc.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in Blockchain class.")
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

                    if hasattr(bc, method):
                        getattr(bc, method)(*parsed_args)
                        bc.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in Blockchain class.")

                else:
                    # No arguments, e.g., accrue_interest
                    method = line
                    if hasattr(bc, method):
                        getattr(bc, method)()
                        bc.pretty_print(precise=is_precise)
                    else:
                        log.error(f"Error: Method '{method}' not found in Blockchain class.")

        except Exception as e:
            log.error(f"Error processing line '{line}': {e}")

# Run the main function if the script is executed directly
if __name__ == "__main__":
    main()