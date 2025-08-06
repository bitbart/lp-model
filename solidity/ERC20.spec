rule transfer_invariants(address recipient, uint256 amount) {
    env e;
    require amount > 0;
    require e.msg.sender != recipient;

    uint256 old_supply = totalSupply(e);
    uint256 old_sender_balance = balanceOf(e, e.msg.sender);
    uint256 old_recipient_balance = balanceOf(e, recipient);

    transfer(e, recipient, amount);

    uint256 new_supply = totalSupply(e);
    uint256 new_sender_balance = balanceOf(e, e.msg.sender);
    uint256 new_recipient_balance = balanceOf(e, recipient);
    
    assert (new_supply == old_supply);
    assert (new_sender_balance == old_sender_balance - amount);
    assert (new_recipient_balance == old_recipient_balance + amount);
}

rule transferFrom_invariants(address sender, address recipient, uint256 amount) {
    env e;
    require sender != recipient && amount > 0;

    uint256 old_supply = totalSupply(e);
    uint256 old_allowance = allowance(e, sender, e.msg.sender);
    uint256 old_sender_balance = balanceOf(e, sender);
    uint256 old_recipient_balance = balanceOf(e, recipient);
    
    transferFrom(e, sender, recipient, amount);

    uint256 new_supply = totalSupply(e);
    uint256 new_allowance = allowance(e, sender, e.msg.sender);
    uint256 new_sender_balance = balanceOf(e, sender);
    uint256 new_recipient_balance = balanceOf(e, recipient);
    
    assert (new_supply == old_supply);
    assert (new_allowance == old_allowance - amount);
    assert (new_sender_balance == old_sender_balance - amount);
    assert (new_recipient_balance == old_recipient_balance + amount);
}

 rule approve_invariants(address spender, uint256 amount) {
        env e;
        require e.msg.sender != spender;

        approve(e, spender, amount);

        assert allowance(e, e.msg.sender, spender) == amount;
    }