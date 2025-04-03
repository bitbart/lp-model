# Unit tests for the Blockchain model
# Usage: pytest test_blockchain.py

import pytest
from math import isclose

from blockchain import Blockchain

"""
Deposit tests
"""

def test_deposit1():
    b = Blockchain()
    b.faucet("A", 100, "ETH")
    b.deposit("A", 100, "ETH")
    assert(b.lastReverted == False)
    assert(b.get_tokens("A","ETH") == 0)

def test_deposit2():
    b = Blockchain()
    b.faucet("A", 100, "ETH")
    b.deposit("A", 101, "ETH")
    assert(b.lastReverted == True)
