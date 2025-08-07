rule deposit_additivity {
    env e1;
    env e2;
    env e3;
    address token;
    uint amount1;
    uint amount2;
    uint amount3;

    storage initial = lastStorage;

    require e1.msg.sender == e2.msg.sender;

    deposit(e1, amount1, token);
    deposit(e2, amount2, token);

    storage s12 = lastStorage;

    require e3.msg.sender == e1.msg.sender;
    require amount3 == amount1 + amount2;

    deposit(e3, amount3, token) at initial;
    storage s3 = lastStorage;

    // checks equality of the following:
    // - the values in storage for all contracts,
    // - the balances of all contracts,
    // - the state of all ghost variables and functions
    // https://docs.certora.com/en/latest/docs/cvl/expr.html#comparing-storage
    // however, the experiments show that also the account balances are checked

    assert s12 == s3;
}
