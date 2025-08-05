# Lending Protocols simulator & analysis

## Prerequisites

### LP simulator

### Unit tests (pytest)
```bash
pip3 install -U pytest
```

### Property-based testing (Hypothesis)

```bash
pip3 install hypothesis
```

### Statistical model checking (MultiVeStA)

```bash
pip3 install numpy
pip3 install matplotlib
pip3 install py4j
sudo apt install openjdk-11-jdk --fix-missing
```

## Usage

### LP simulator

All the commands below must be executed from the `lp-simulator` folder.

To execute a sequence of transactions:
```bash
python blockchain.py traces/trace1.txt
```

To execute a sequence of transactions (LP-only, ignoring users' wallets):
```bash
python lp.py traces/trace1.txt
```

### Unit testing

```bash
pytest test_lp.py
pytest test_blockchain.py
```

### Property-based testing

```bash
pytest pbt_lp.py
```

### Statistical model checking

```bash
java -jar multivesta.jar -c -m MV_python_integrator.py -sm true -f q1.multiquatex -l 2 -sots 1 -sd vesta.python.simpy.SimPyState -vp true -bs 30 -ds [10] -a 0.05 -otherParams "python3"
```