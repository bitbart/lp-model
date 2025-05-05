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

For statistical model checking with MultiVeStA:
```bash
pip3 install numpy
pip3 install matplotlib
pip3 install py4j
sudo apt install openjdk-11-jdk --fix-missing
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

To execute statistical model checking:
```bash
java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f q1.multiquatex -l 2 -sots 1 -sd vesta.python.simpy.SimPyState -vp true -bs 30 -ds [10] -a 0.05 -otherParams "python3"
```