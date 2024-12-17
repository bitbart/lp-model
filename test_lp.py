# Unit tests for the LP model
# Usage: pytest test_lp.py

import pytest
from math import isclose

from lp import LP

def test_deposit1():
    g = LP()
    g.deposit("A", 100, "ETH")
    assert(g.lastReverted == False)
    assert(g.get_reserves("ETH") == 100)
    assert(g.get_minted("ETH","A") == 100)
    assert(g.get_debts("ETH","A") == 0)

def test_deposit2():
    g = LP()
    g.deposit("A", 100, "ETH")
    assert(g.lastReverted == False)
    g.deposit("A", 50, "ETH")
    assert(g.lastReverted == False)
    assert(g.get_reserves("ETH") == 150)
    assert(g.get_minted("ETH","A") == 150)
    assert(g.get_debts("ETH","A") == 0)

def test_deposit3():
    g = LP()
    g.deposit("A", 50, "T0")
    assert(g.lastReverted == False)
    g.deposit("B", 50, "T1")
    assert(g.lastReverted == False)
    assert(g.get_reserves("T0") == 50)
    assert(g.get_reserves("T1") == 50)
    assert(g.get_minted("T0","A") == 50)
    assert(g.get_minted("T1","A") == 0)
    assert(g.get_minted("T0","B") == 0)
    assert(g.get_minted("T1","B") == 50)
    assert(g.get_debts("T0","A") == 0)
    assert(g.get_debts("T1","A") == 0)
    assert(g.get_debts("T0","B") == 0)
    assert(g.get_debts("T1","B") == 0)

def test_deposit4():
    g = LP()
    g.deposit("A", 100, "T0")
    assert(g.lastReverted == False)
    g.deposit("A", 150, "T1")
    assert(g.lastReverted == False)
    g.deposit("B",  50, "T0")
    assert(g.lastReverted == False)
    g.deposit("B",  50, "T2")
    assert(g.lastReverted == False)
    g.deposit("C", 100, "T2")
    assert(g.lastReverted == False)

    assert(g.get_reserves("T0") == 150)
    assert(g.get_reserves("T1") == 150)
    assert(g.get_reserves("T2") == 150)

    assert(g.get_minted("T0","A") == 100)
    assert(g.get_minted("T1","A") == 150)
    assert(g.get_minted("T2","A") == 0)

    assert(g.get_minted("T0","B") == 50)
    assert(g.get_minted("T1","B") == 0)
    assert(g.get_minted("T2","B") == 50)

    assert(g.get_minted("T0","C") == 0)
    assert(g.get_minted("T1","C") == 0)
    assert(g.get_minted("T2","C") == 100)

    assert(g.get_debts("T0","A") == 0)
    assert(g.get_debts("T1","A") == 0)
    assert(g.get_debts("T2","A") == 0)

    assert(g.get_debts("T0","B") == 0)
    assert(g.get_debts("T1","B") == 0)
    assert(g.get_debts("T2","B") == 0)

    assert(g.get_debts("T0","C") == 0)
    assert(g.get_debts("T1","C") == 0)
    assert(g.get_debts("T2","C") == 0)

def test_borrow1():
    g = LP()
    g.set_price("ETH", 1)
    g.deposit("A", 100, "ETH")
    assert(g.lastReverted == False)
    g.borrow("A", 50, "ETH")
    assert(g.lastReverted == False)

    assert(g.get_reserves("ETH") == 50)
    assert(g.get_minted("ETH","A") == 100)
    assert(g.get_debts("ETH","A") == 50)

def test_borrow2():
    g = LP()

    g.deposit("A", 100, "T0")
    assert(g.lastReverted == False)
    g.deposit("A", 150, "T1")
    assert(g.lastReverted == False)
    g.deposit("B",  50, "T0")
    assert(g.lastReverted == False)
    g.deposit("B",  50, "T2")
    assert(g.lastReverted == False)
    g.deposit("C", 100, "T2")
    assert(g.lastReverted == False)

    g.borrow("B", 50, "T1")
    assert(g.lastReverted == False)

    assert(g.get_reserves("T1") == 100)
    assert(g.get_debts("T1","B") == 50)

    g.borrow("C", 30, "T0")
    assert(g.lastReverted == False)

    assert(g.get_reserves("T0") == 120)
    assert(g.get_debts("T0","C") == 30)

    g.borrow("C", 30, "T1")
    assert(g.lastReverted == False)

    assert(g.get_reserves("T1") == 70)
    assert(g.get_debts("T0","C") == 30)
    assert(g.get_debts("T1","A") == 0)
    assert(g.get_debts("T1","B") == 50)
    assert(g.get_debts("T1","C") == 30)

def test_borrow3():
    g = LP()
    g.borrow("A", 1, "T")
    assert(g.lastReverted)

def test_borrow4():
    g = LP()
    g.deposit("B", 1, "T")
    g.borrow("A", 1, "T")
    assert(g.lastReverted)

def test_borrow5():
    g = LP()
    g.deposit('A',1, 'T')
    g.deposit('A',14,'T')
    g.borrow('A', 1, 'T')
    g.borrow('A', 1, 'T')
    g.borrow('A', 1, 'T')
    g.borrow('A', 1, 'T')
    g.borrow('A', 1, 'T')
    xr_pre = g.get_xr()
    g.deposit('A',1, 'T')
    xr_post = g.get_xr()
    for token in xr_pre:
        assert isclose(xr_pre[token], xr_post[token], abs_tol=1e-3)
    # assert(g.get_debts('T','A') == 5)

def test_borrow5():
    g = LP()
    g.deposit('B', 2, 'T')
    assert(g.lastReverted == False)
    g.borrow ('A', 1, 'T')
    assert(g.lastReverted)
    g.deposit('A', 2, 'U')
    assert(g.lastReverted == False)
    g.borrow ('A', 1, 'T')
    assert(g.lastReverted == False)
    g.borrow ('A', 1, 'T')
    assert(g.lastReverted)

    xr_pre = g.get_xr()
    g.deposit('A', 1, 'T')
    assert(g.lastReverted == False)
    xr_post = g.get_xr()
    for token in xr_pre:
        assert isclose(xr_pre[token], xr_post[token], abs_tol=1e-3)

def test_accrue1():
    g = LP()
    g.set_price("T0", 1)
    g.set_price("T1", 1)
    g.set_price("T2", 1)

    g.deposit("A", 100, "T0")
    g.deposit("A", 150, "T1")
    g.deposit("B",  50, "T0")
    g.deposit("B",  50, "T2")
    g.deposit("C", 100, "T2")

    g.borrow("B", 50, "T1")
    g.borrow("C", 30, "T0")
    g.borrow("C", 30, "T1")

    assert(g.get_debts("T0","C") == 30)
    assert(g.get_debts("T1","B") == 50)
    assert(g.get_debts("T1","C") == 30)

    g.accrue_interest()
    assert(1.8 <= g.collateral("B") <= 1.9)
    assert(1.4 <= g.collateral("C") <= 1.5)
    assert(32 <= g.get_debts("T0","C") <= 34)
    assert(g.get_debts("T1","B") == 56)
    assert(33 <= g.get_debts("T1","C") <= 34)

    g.accrue_interest()
    assert(1.6 <= g.collateral("B") <= 1.7)
    assert(1.3 <= g.collateral("C") <= 1.4)

def test_repay1():
    g = LP()
    g.set_price("T0", 1)
    g.set_price("T1", 1)
    g.set_price("T2", 1)

    g.deposit("A", 100, "T0")
    g.deposit("A", 150, "T1")
    g.deposit("B",  50, "T0")
    g.deposit("B",  50, "T2")
    g.deposit("C", 100, "T2")

    g.borrow("B", 50, "T1")
    g.borrow("C", 30, "T0")
    g.borrow("C", 30, "T1")

    g.accrue_interest()
    g.accrue_interest()
    g.accrue_interest()

    g.repay("C", 15, "T0")
    assert(g.get_reserves("T0") == 135)
    assert(20 <= g.get_debts("T0","C") <= 30)

def test_redeem1():
    g = LP()
    g.set_price("T0", 1)
    g.set_price("T1", 1)
    g.set_price("T2", 1)

    g.deposit("A", 100, "T0")
    g.deposit("A", 150, "T1")
    g.deposit("B",  50, "T0")
    g.deposit("B",  50, "T2")
    g.deposit("C", 100, "T2")

    g.borrow("B", 50, "T1")
    g.borrow("C", 30, "T0")
    g.borrow("C", 30, "T1")

    g.accrue_interest()
    g.accrue_interest()
    # g.accrue_interest()

    g.repay("C", 15, "T0")
    assert(g.get_minted("T2", "B") >= 11)
    g.redeem("B", 8, "T2")
    assert(g.get_reserves("T2") == 142)
