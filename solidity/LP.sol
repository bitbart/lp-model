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

    IERC20 public tok0;
    IERC20 public tok1;

    address[] public tokens;

    // Constructor accepts arrays of borrow tokens and collateral tokens
    constructor(ERC20 _tok0, ERC20 _tok1) {
        tok0 = _tok0;
        tok1 = _tok1;
        require(tok0 != tok1);
        tokens.push(address(tok0));
        tokens.push(address(tok1));
    }

    // XR(t) returns the exchange rate for token t (multiplied by 1000000)
    function XR(address token) public view returns (uint256) {
        if (totCredit[token] == 0) {
            return 1000000;
        }
        else {
            return ((reserves[token] + totDebit[token]) * 1000000) / totCredit[token];
        }    
    }

    function valCredit(address a) public view returns (uint256) {
        uint256 val = 0;
        for (uint i = 0; i < tokens.length; i++) {
            val += credit[tokens[i]][a];
        }
        return val;
    }

    function valDebit(address a) public view returns (uint256) {
        uint256 val = 0;
        for (uint i = 0; i < tokens.length; i++) {
            val += debit[tokens[i]][a];
        }
        return val;
    }

    function isCollateralized(address a) public view returns (bool) {
        if (valDebit(a) == 0) {
            return true; // No debt, so always collateralized
        }
        // health factor (multiplied by 10e6)
        uint256 hf = (valCredit(a) * tLiq) / valDebit(a);
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
        uint256 amount_credit = (amount * 1000000) / XR(token_addr);
        credit[token_addr][msg.sender] += amount_credit;
        totCredit[token_addr] += amount_credit;
    }

    function borrow(uint amount, address token_addr) public {
        require(amount > 0, "Borrow: amount must be greater than zero");
        require(
            isValidToken(token_addr),
            "Borow: invalid token"
        );

        // Check if the reserves are sufficient
        require(reserves[token_addr] >= amount, "Borrow: insufficient reserves");

        // Transfer tokens to the borrower
        ERC20 token = ERC20(token_addr);
        token.transfer(msg.sender, amount);

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
}