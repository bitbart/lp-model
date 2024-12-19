# Stateful property-based tests with Hypothesis
# Usage: pytest pbt_lp.py

from lp import LP

from hypothesis import note, assume, settings
from hypothesis.strategies import *
from hypothesis.stateful import rule, invariant, precondition, RuleBasedStateMachine

import pytest
import math

class WrappedLP(LP):
    def __init__(self):
        super().__init__()
        # super(LP, self).__init__()

    """
    Method wrappers for the LP model
    """

    @rule(token=text(alphabet="TUVXYZ",min_size=1,max_size=1), price=floats(min_value=0.1,max_value=2.0))
    def set_price(self, token, price):
        super().set_price(token, price)

    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def deposit(self, address, amount, token):
        super().deposit(address, amount, token)

    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def borrow(self, address, amount, token):
        super().borrow(address, amount, token)

    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def repay(self, address, amount, token):
        super().repay(address, amount, token)

    @rule()
    def accrue_interest(self):
        super().accrue_interest()

    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def redeem(self, address, amount, token):
        super().redeem(address, amount, token)

    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), 
          amount_debt=integers(min_value=1,max_value=100), 
          token_debt=text(alphabet="TUVXYZ",min_size=1,max_size=1),
          address_debtor=text(alphabet="ABCDEF",min_size=1,max_size=1),
          token_minted=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def liquidate(self, address, amount_debt, token_debt, address_debtor, token_minted):
        super().liquidate(address, amount_debt, token_debt, address_debtor, token_minted)

    """
    Rule: 
        test_deposit_notrevert 
        checks that the deposit method does not revert when the deposit amount is greater than zero
    """
    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def test_deposit_notrevert(self, address, amount, token):	
        self.deposit(address, amount, token)
        assert(self.lastReverted == False)

    """
    Rule: 
        test_deposit_XR
        checks that the exchange rate (XR) of all tokens is preserved by a deposit
    """
    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def test_deposit_XR(self, address, amount, token):	
        xr_pre = super().get_xr()
        super().deposit(address, amount, token)
        xr_post = super().get_xr()
        assert xr_post == xr_pre

    """
    Rule: 
        test_borrow_XR
        checks that the exchange rate (XR) of all tokens is preserved by a borrow
    """
    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def test_borrow_XR(self, address, amount, token):	
        xr_pre = super().get_xr()
        super().borrow(address, amount, token)
        xr_post = super().get_xr()
        assert xr_post == xr_pre

    """
    Rule: 
        test_repay_XR
        checks that the exchange rate (XR) of all tokens is preserved by a repay
    """
    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def test_repay_XR(self, address, amount, token):	
        xr_pre = super().get_xr()
        super().repay(address, amount, token)
        xr_post = super().get_xr()
        assert xr_post == xr_pre

    """
    Rule: 
        test_redeem_XR
        checks that the exchange rate (XR) of all tokens is preserved by a redeem
    """
    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), amount=integers(min_value=1,max_value=100), token=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def test_redeem_XR(self, address, amount, token):	
        xr_pre = super().get_xr()
        super().redeem(address, amount, token)
        xr_post = super().get_xr()
        assert xr_post == xr_pre

    """
    Rule: 
        test_liquidate_XR
        checks that the exchange rate (XR) of all tokens is preserved by a liquidate
    """
    @rule(address=text(alphabet="ABCDEF",min_size=1,max_size=1), 
          amount_debt=integers(min_value=1,max_value=100), 
          token_debt=text(alphabet="TUVXYZ",min_size=1,max_size=1),
          address_debtor=text(alphabet="ABCDEF",min_size=1,max_size=1),
          token_minted=text(alphabet="TUVXYZ",min_size=1,max_size=1))
    def test_liquidate_XR(self, address, amount_debt, token_debt, address_debtor, token_minted):
        xr_pre = super().get_xr()
        super().liquidate(address, amount_debt, token_debt, address_debtor, token_minted)
        xr_post = super().get_xr()
        assert xr_post == xr_pre

    """
    Rule: 
        test_accrue_interest_XR
        checks that the exchange rate (XR) of all tokens increases upon interest accruals
    """
    @rule()
    def test_accrue_interest_XR(self):	
        xr_pre = super().get_xr()
        super().accrue_interest()
        xr_post = super().get_xr()
        for token in xr_pre:
            assert xr_pre[token] < xr_post[token]

    @invariant()
    def test_XR_geq_1(self):	
        xr = super().get_xr()
        for token in xr:
            assert xr[token] >= 1

TestWrappedLP = WrappedLP.TestCase

WrappedLP.TestCase.settings = settings(
    max_examples=5000, stateful_step_count=20
)
