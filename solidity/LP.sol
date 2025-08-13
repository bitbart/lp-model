// SPDX-License-Identifier: GPL-3.0-only
pragma solidity >= 0.8.2;

import "./ERC20.sol";

contract LP {
    // workaround for bug in solc v0.8.30
    address constant ZERO_ADDRESS = address(0x0000000000000000000000000000000000000000);

    uint256 public immutable tLiq = 666666; // Collateralization threshold (multiplied by 1000000)

    // token reserves in the LP
    mapping(address => uint256) public reserves; // token -> amount

    // amount of credit tokens held by each user
    mapping(address => mapping(address => uint256)) public credit; // token -> user -> amount 
    // amount of debit tokens held by each user
    mapping(address => mapping(address => uint256)) public debit; // token -> user -> amount

    // total amount of credit tokens (used to compute exchange rate)
    mapping(address => uint256) public totCredit; // token -> amount
    // total amount of debit tokens (used to compute exchange rate)
    mapping(address => uint256) public totDebit; // token -> amount

    // last block when interest was accrued for eash borrower
    mapping (address token => mapping (address borrower => uint256 block)) lastAccrued;

    // last block when totDebit was updated (used to compute XR)
    mapping (address token => uint256 block) lastTotAccrued;

    // token prices
    mapping (address token => uint256 price) prices;

    IERC20 public tok0;
    IERC20 public tok1;

    address[] public tokens;

    uint256 public immutable interestRatePerBlock = 10000; // interest rate per time unit * 1e6 (1%)

    // Constructor accepts arrays of borrow tokens and collateral tokens
    constructor(ERC20 _tok0, ERC20 _tok1) {
        tok0 = _tok0;
        tok1 = _tok1;
        require(tok0 != tok1);
        tokens.push(address(tok0));
        tokens.push(address(tok1));

        // in this version of the contract, token prices are constant
        prices[address(tok0)] = 1;
        prices[address(tok1)] = 2;
    }

    // Update totDebit[token] by accruing interest for all borrowers
    function _accrueTotInt(address token) internal {
        uint lastTime = lastTotAccrued[token];
        if (lastTime == 0) {    // happens on first deposit
            lastTotAccrued[token] = block.timestamp;
            return;
        }
    
        uint elapsed = block.number - lastTime;
        if (elapsed > 0 && totDebit[token] > 0) {
            // Simple interest: debt += debt * rate * time
            uint interest = (totDebit[token] * interestRatePerBlock * elapsed) / 1e6;
            totDebit[token] += interest;
        }

        lastTotAccrued[token] = block.timestamp;
    }

    // Update debit[token][borrower] by accruing interest for a given borrower
    function _accrueInt(address token, address borrower) internal {
        uint lastTime = lastAccrued[token][borrower];
        if (lastTime == 0) {    // happens on first deposit
            lastAccrued[token][borrower] = block.timestamp;
            return;
        }
    
        uint elapsed = block.number - lastTime;
        if (elapsed > 0 && debit[token][borrower] > 0) {
            // Simple interest: debt += debt * rate * time
            uint interest = (debit[token][borrower] * interestRatePerBlock * elapsed) / 1e6;
            debit[token][borrower] += interest;
        }

        lastAccrued[token][borrower] = block.timestamp;
    }

    function XR_def(uint credits, uint debits, uint res) internal pure returns (uint) {
        if (credits == 0) {
            return 1000000; // Default exchange rate if no credits
        } else {
            return ((res + debits) * 1000000) / credits;
        }
    }

    // XR(t) returns the exchange rate for token t (multiplied by 1000000)
    // Assumes that interests on totDebit[token] have been accrued
    function XR(address token) public view returns (uint) {
        require (isValidToken(token), "Invalid token");
        return XR_def(totCredit[token], totDebit[token], reserves[token]);
    }

    // Assumes that interests on totDebit have been accrued
    function valCredit(address a) public view returns (uint256) {
        uint256 val = 0;
        for (uint i = 0; i < tokens.length; i++) {
            val += credit[tokens[i]][a] * XR(tokens[i]) * getPrice(tokens[i]);
        }
        return val;
    }

    // Assumes that interests on all debits of borrower a have been accrued
    function valDebit(address a) public view returns (uint256) {
        uint256 val = 0;
        for (uint i = 0; i < tokens.length; i++) {
            val += debit[tokens[i]][a] * getPrice(tokens[i]);
        }
        return val;
    }

    // Assumes that interests on totDebit and on all debits of borrower a have been accrued
    function isCollateralized(address a) public view returns (bool) {
        uint vdA = valDebit(a); 
        if (vdA == 0) {
            return true; // No debt, so always collateralized
        }
        // health factor (multiplied by 10e6)
        uint256 hf = (valCredit(a) * tLiq) / vdA;
        return (hf >= 1000000);
    }

    function isValidToken(address token) public view returns (bool) {
        for (uint i = 0; i < tokens.length; i++) {
            if (tokens[i] == token) {
                return true;
            }
        }
        return false;
        // return (token == address(tok0) || token == address(tok1));
    }

    function deposit(uint amount, address token_addr) public {
        require(amount > 0, "Deposit: amount must be greater than zero");
        require(
            isValidToken(token_addr),
            "Deposit: invalid token"
        );
        ERC20 token = ERC20(token_addr);

        token.transferFrom(msg.sender, address(this), amount);
        reserves[token_addr] += amount;

        // accrues interests on totDebit[token] before computing XR 
        _accrueTotInt(token_addr);
        uint256 amount_credit = (amount * 1000000) / XR(token_addr);
 
        credit[token_addr][msg.sender] += amount_credit;
        totCredit[token_addr] += amount_credit;
    }

    function borrow(uint amount, address token_addr) public {
        require(amount > 0, "Borrow: amount must be greater than zero");
        require(
            isValidToken(token_addr),
            "Borrow: invalid token"
        );

        // Check if the reserves are sufficient
        require(reserves[token_addr] >= amount, "Borrow: insufficient reserves");

        // Transfer tokens to the borrower
        ERC20 token = ERC20(token_addr);
        token.transfer(msg.sender, amount);

        // accrues all interests before computing collateralization
        for (uint i = 0; i < tokens.length; i++) {
            _accrueTotInt(tokens[i]);
            _accrueInt(tokens[i], msg.sender);
        }

        reserves[token_addr] -= amount;
        debit[token_addr][msg.sender] += amount;
        totDebit[token_addr] += amount;

        // Check if the borrower is collateralized
        require(isCollateralized(msg.sender), "Borrow: user is not collateralized");
    }

    function repay(uint amount, address token_addr) public {
        require(amount > 0, "Repay: amount must be greater than zero");
        require(
            isValidToken(token_addr),
            "Repay: invalid token"
        );

        require(
            debit[token_addr][msg.sender] >= amount,
            "Repay: insufficient debts"
        );

        ERC20 token = ERC20(token_addr);
        token.transferFrom(msg.sender, address(this), amount);

        reserves[token_addr] += amount;
        debit[token_addr][msg.sender] -= amount;
        totDebit[token_addr] -= amount;
    }

    function redeem(uint amount, address token_addr) public {
        require(amount > 0, "Redeem: amount must be greater than zero");
        require(
            isValidToken(token_addr),
            "Redeem: invalid token"
        );

        require(
            credit[token_addr][msg.sender] >= amount,
            "Redeem: insufficient credits"
        );

        // accrues all interests before computing XR and collateralization
        for (uint i = 0; i < tokens.length; i++) {
            _accrueTotInt(tokens[i]);
            _accrueInt(tokens[i], msg.sender);
        }

        uint amount_rdm = (amount * XR(token_addr)) / 1000000;
        require(
            reserves[token_addr] >= amount_rdm,
            "Redeem: insufficient reserves"
        );

        ERC20 token = ERC20(token_addr);
        token.transfer(msg.sender, amount_rdm);

        reserves[token_addr] -= amount_rdm;
        credit[token_addr][msg.sender] -= amount;
        totCredit[token_addr] -= amount;
    
        // Check if the user is collateralized
        require(isCollateralized(msg.sender), "Redeem: user is not collateralized");
    }

    function liquidate(uint amount, address token_debit, address debtor, address token_credit) public pure {
        // in this version, liquidate is disabled
    }

    function getPrice(address token_addr) public view returns (uint256) {
        require(
            isValidToken(token_addr),
            "Redeem: invalid token"
        );
        return prices[token_addr];
    }
}