// SPDX-License-Identifier: GPL-3.0-only

// import "erc20.spec";

rule deposit_post {
    env e;
    address t0;
    address t1;
    address a;
    address b;
    uint amt;

    require (a != b && t0 != t1);
    require (e.msg.sender == a);
    require (currentContract.isValidToken(e, t0));

    require (currentContract.lastAccrued[t0][e.msg.sender] == e.block.number);
    require (currentContract.lastAccrued[t1][e.msg.sender] == e.block.number);
    require (currentContract.lastTotAccrued[t0] == e.block.number);
        
    require (currentContract.reserves[t0] == 0);

    uint old_reserves_t0 = currentContract.reserves[t0];   
    uint old_reserves_t1 = currentContract.reserves[t1];
    uint old_credit_t0_a = currentContract.credit[t0][a];
    uint old_credit_t1_a = currentContract.credit[t1][a];
    uint old_credit_t0_b = currentContract.credit[t0][b];
    uint old_credit_t1_b = currentContract.credit[t1][b];

    deposit(e, amt, t0);

    uint new_reserves_t0 = currentContract.reserves[t0];   
    uint new_reserves_t1 = currentContract.reserves[t1];
    uint new_credit_t0_a = currentContract.credit[t0][a];
    uint new_credit_t1_a = currentContract.credit[t1][a];
    uint new_credit_t0_b = currentContract.credit[t0][b];
    uint new_credit_t1_b = currentContract.credit[t1][b];

    uint xr_t0 = currentContract.XR(e, t0);
 
    // assert(xr_t0 >= 1000000);

    assert(new_reserves_t0 == old_reserves_t0 + amt);
    assert(new_reserves_t1 == old_reserves_t1);

    // check!
    assert(new_credit_t0_a >= old_credit_t0_a + (amt * 1000000) / xr_t0);

    assert(new_credit_t1_a == old_credit_t1_a);

    assert(new_credit_t0_b == old_credit_t0_b);
    assert(new_credit_t1_b == old_credit_t1_b);
}
