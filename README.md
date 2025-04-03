# Lending Protocols simulator

## Prerequisites

For unit tests with pytest:
```bash
pip3 install -U pytest
```

For property-based testing with Hypothesis:
```bash
pip3 install hypothesis
```

## Usage

To execute a sequence of transactions:
```bash
python blockchain.py trace1.txt
```

To execute a sequence of transactions (LP-only, ignoring users' wallets):
```bash
python lp.py trace1.txt
```

To execute unit tests:
```bash
pytest test_lp.py
pytest test_blockchain.py
```

To execute property-based tests:
```bash
pytest pbt_lp.py
```