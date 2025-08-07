// SPDX-License-Identifier: GPL-3.0-only
pragma solidity >= 0.8.2;

// solc LP_solcmc.sol --model-checker-engine chc --model-checker-targets assert --model-checker-show-unproved  --model-checker-solvers eld --model-checker-ext-calls trusted

import "./LP.sol";

contract LPsolcmc is LP {

    constructor(ERC20 _tok0, ERC20 _tok1)
        LP(_tok0, _tok1) {}


    // Lemma 3.3: Ensure that the total credit and debit balances are consistent
    function invariant_credit_debit_zero() public view {
        for (uint i = 0; i < tokens.length; i++) {
            address t = tokens[i];
            require(
                totCredit[t] != 0 ||
                (totDebit[t] == 0 && reserves[t] == 0),
                "Inconsistent total credit/debit amounts"
            );
        }
    }

    // Lemma 3.4 / deposit
    // function rule_deposit_xr(
    //     uint256 amount,
    //     address t
    // ) public {
    //     uint256 old_xr = XR(t);
    //     deposit(amount, t);
    //     uint256 xr = XR(t);
    //     assert(xr == old_xr);
    // }

    // Lemma 3.4 / borrow
    // function rule_borrow_xr(
    //     uint256 amount,
    //     address t
    // ) public {
    //     uint256 old_xr = XR(t);
    //     borrow(amount, t);
    //     uint256 xr = XR(t);
    //     assert(xr == old_xr);
    // }

    // Lemma 3.5
    // function invariant_xr_geq_one() public view {
    //     for (uint i = 0; i < tokens.length; i++) {
    //         address t = tokens[i];
    //         assert(XR(t) >= 1000000);
    //     }
    // }

    function rule_deposit_assets_transfer(
        uint256 amount,
        address t
    ) public {
        uint256 old_sender_balance = IERC20(t).balanceOf(msg.sender);
        uint256 old_contract_balance = IERC20(t).balanceOf(address(this));
        uint256 old_reserves = reserves[t];

        deposit(amount, t);

        uint256 sender_balance = IERC20(t).balanceOf(msg.sender);
        uint256 contract_balance = IERC20(t).balanceOf(address(this));

        assert(sender_balance == old_sender_balance - amount);
        assert(contract_balance == old_contract_balance + amount);
        assert(reserves[t] == old_reserves + amount);
    }

    function rule_borrow_assets_transfer(
        uint256 amount,
        address t
    ) public {
        uint256 old_sender_balance = IERC20(t).balanceOf(msg.sender);
        uint256 old_contract_balance = IERC20(t).balanceOf(address(this));
        uint256 old_reserves = reserves[t];

        borrow(amount, t);

        uint256 sender_balance = IERC20(t).balanceOf(msg.sender);
        uint256 contract_balance = IERC20(t).balanceOf(address(this));

        assert(sender_balance == old_sender_balance + amount);
        assert(contract_balance == old_contract_balance - amount);
        assert(reserves[t] == old_reserves - amount);
    }

    function rule_repay_assets_transfer(
        uint256 amount,
        address t
    ) public {
        uint256 old_sender_balance = IERC20(t).balanceOf(msg.sender);
        uint256 old_contract_balance = IERC20(t).balanceOf(address(this));
        uint256 old_reserves = reserves[t];

        repay(amount, t);

        uint256 sender_balance = IERC20(t).balanceOf(msg.sender);
        uint256 contract_balance = IERC20(t).balanceOf(address(this));

        assert(sender_balance == old_sender_balance - amount);
        assert(contract_balance == old_contract_balance + amount);
        assert(reserves[t] == old_reserves + amount);
    }
}