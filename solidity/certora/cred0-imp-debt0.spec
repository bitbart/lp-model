// Lemma 3.3
invariant cred0_imp_debt0(address token)
    currentContract.totCredit[token] == 0 => 
    (currentContract.totDebit[token] == 0 && currentContract.reserves[token] == 0);
