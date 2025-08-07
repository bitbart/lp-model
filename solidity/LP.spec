// SPDX-License-Identifier: GPL-3.0-only

// import "erc20.spec";

rule trace1 {
    env e1;
    address t0;
    address t1;
    address a;
    address b;
    require(a != b && a!=0 && b!=0 && a!=currentContract && b!=currentContract);
    require(t0 != t1);

    require (currentContract.reserves[t0] == 0);
    require (currentContract.reserves[t1] == 0);
    require (currentContract.totCredit[t0] == 0);
    require (currentContract.totCredit[t1] == 0);
    require (currentContract.totDebit[t0] == 0);
    require (currentContract.totDebit[t1] == 0);

    // A:deposit(50:T0)

    require(e1.msg.sender == a);
    require(e1.msg.value == 0);

    uint reserve_t0_0 = currentContract.reserves[t0];   
    uint reserve_t1_0 = currentContract.reserves[t1];
    uint credit_t0_a_0 = currentContract.credit[t0][a];

    deposit(e1, 50, t0); 
    
    uint reserve_t0_1 = currentContract.reserves[t0];
    uint reserve_t1_1 = currentContract.reserves[t1];   
    uint credit_t0_a_1 = currentContract.credit[t0][a];
    uint credit_t1_b_1 = currentContract.credit[t1][b];

    // B:deposit(50:T1)

    env e2;
    require(e2.msg.sender == b);
    require(e2.msg.value == 0);

    deposit(e2, 50, t1);
    
    uint reserve_t0_2 = currentContract.reserves[t0];
    uint reserve_t1_2 = currentContract.reserves[t1];
    uint credit_t1_b_2 = currentContract.credit[t1][b];

    // B:borrow(30:T0)

    env e3;
    require(e3.msg.sender == b);
    require(e3.msg.value == 0);

    borrow(e3, 30, t0);
    
    uint reserve_t0_3 = currentContract.reserves[t0];
    uint reserve_t1_3 = currentContract.reserves[t1];

    assert(reserve_t0_1 == reserve_t0_0 + 50);
    assert(reserve_t1_1 == reserve_t1_0);
    assert(credit_t0_a_1 == credit_t0_a_0 + 50);
            
    assert(reserve_t0_2 == reserve_t0_1);
    assert(reserve_t1_2 == reserve_t1_1 + 50);
    assert(credit_t1_b_2 == credit_t1_b_1 + 50);

    assert(reserve_t0_3 == reserve_t0_2 - 30);
    assert(reserve_t1_3 == reserve_t1_2);
}
