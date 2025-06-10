from z3 import *
import itertools, pprint
from collections.abc import Iterable

INFTY = 100000
USE_LIN_UTILIZATION_INT_RATE = True


def print_model(m, i, state_variables, transition_variables):
    dont_print = []
    #dont_print = ['Coll', 'Health', 'W','Ww', 'Wc', 'Wd', 'C', 'D']
    print(f"Tliq: {m[Tliq]}")
    print(f"Rliq: {m[Rliq]}")
    if USE_LIN_UTILIZATION_INT_RATE:
        print(f"alfa: {m[alfa]}")
        print(f"beta: {m[beta]}")
    m_d = {str(d): (m[d].as_decimal(2) if type(m[d])==RatNumRef  else m[d] ) for d in m}
    #m_d = {str(d): (m[d] if type(m[d])==RatNumRef  else m[d] ) for d in m}
    state_vars = list(state_variables.keys())
    trans_vars = list(transition_variables.keys())
    for v in trans_vars + state_vars:
        if v in dont_print:
            continue
        print("\n",v.replace("tx_","")[:6], end="\t")
        m_d_v = {}
        l_v = []
        for key in m_d:
            if str(key).startswith(f"{v}_"):
            #if f"{v}_" in str(key):
                m_d_v[str(key)] = m_d[key]
                l_v.append((m_d[key]))
        keys = list(m_d_v.keys())
        keys.sort()
        first_key = str(list(m_d_v.keys())[0])
        #print(f"{first_key=}")
        if "_t" not in first_key and "_u" in first_key and not v in trans_vars:  # var only depends on user
            #print("var only depends on user")
            for user in Users:
                print(f'U{user}\t\t','\t'.join([str(m_d[f"{v}_s{state}_u{user}"]) for state in States[:i]]), end="\n\t")
        elif "_t" in first_key and "_u" not in first_key and not v in trans_vars :  # var only depends on token
            #print("var only depends on token")
            for token in Tokens:
                print(f'T{token}\t\t','\t'.join([str(m_d[f"{v}_s{state}_t{token}"]) for state in States[:i]]), end="\n\t")
        elif "_t" in first_key and "_u" in first_key  and not v in trans_vars:  # var depends on both token and user
            #print("var depends on both users and tokens")
            for token in Tokens:
                print(f'T{token}', end="")
                for user in Users:
                    print(f'\tU{user}\t','\t'.join([str(m_d[f"{v}_s{state}_t{token}_u{user}"]) for state in States[:i]]), end="\n\t")
        else:   
            print(f'\t\t','\t'.join([str(m_d[f"{v}_s{state}"]) for state in States[:i-1]]), end="\n\t")
            #print(f'\t\t','\t'.join([str(m_d_v[el]) for el in m_d_v.keys()]), end="\n\t")
                

def flatten(items, seqtypes=(list, tuple)):
    for i, x in enumerate(items):
        while i < len(items) and isinstance(items[i], seqtypes):
            items[i:i+1] = items[i]
    return items

def flatten2(pl):
    if not isinstance(pl[0], list):
        return pl
    old_l = pl
    while(True):
        if not isinstance(old_l[0], list):
            return old_l
        new_fl = list(itertools.chain.from_iterable(old_l))
        if new_fl == old_l:
            break
        else:
            old_l = new_fl
    return new_fl

def printModel(m):
    m_sorted = sorted ([(d, m[d]) for d in m], key = lambda x: str(x[0]))
    print(*m_sorted,sep='\n')


s = Solver()


Max_Steps = 15
States = range(Max_Steps)

# number of users
nUsers = 2
Users = range(nUsers)

# number of tokens
nTokens = 2
Tokens = range(nTokens)


# Liquidation threshold
Tliq = Real('TLiq')
s.add(Tliq > 0)
s.add(Tliq < 1)

# Reward factor
Rliq = Real('RLiq')
s.add(Rliq > 1)


# wallets
w = [[[Real("w_s%s_t%s_u%s" % (state, token, user)) for user in Users] for token in Tokens] for state in States]

#print(w[4])

# reserves
r = [[Real("r_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# credits map
c = [[[Real("c_s%s_t%s_u%s" % (state, token, user)) for user in Users] for token in Tokens] for state in States]

# debts map
d = [[[Real("d_s%s_t%s_u%s" % (state, token, user)) for user in Users] for token in Tokens] for state in States]

# credits supply
C = [[Real("C_s%s_t%s" % (state, token)) for token in Tokens] for state in States]


# debts supply
D = [[Real("D_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# price
p = [[Real("p_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# exchange rate
X = [[Real("X_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# Wallet value
Ww = [[Real("Ww_s%s_u%s" % (state, user)) for user in Users] for state in States]

# Credits value
Wc = [[Real("Wc_s%s_u%s" % (state, user)) for user in Users] for state in States]

# Debts value
Wd = [[Real("Wd_s%s_u%s" % (state, user)) for user in Users] for state in States]


# Net worth 
W = [[Real("W_s%s_u%s" % (state, user)) for user in Users] for state in States]

# Collateralization 
Coll = [[Real("Coll_s%s_u%s" % (state, user)) for user in Users] for state in States]

# Health factor 
Health = [[Real("Health_s%s_u%s" % (state, user)) for user in Users] for state in States]

# Interest rate
I = [[Real("I_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# Param for linear utilization interest rate function
alfa, beta = Reals('alfa beta') 
s.add(beta > 0)

# Utilization
U = [[Real("U_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

def state_conditions(w_i, r_i, c_i, d_i,  C_i, D_i, p_i, 
                     X_i, Ww_i, Wc_i, Wd_i, W_i,
                     Coll_i, Health_i, I_i, U_i):
    return And(
        And(flatten([[w_i[token][user] >= 0 for user in Users] for token in Tokens])),
        And(flatten([[c_i[token][user] >= 0 for user in Users] for token in Tokens])),
        And(flatten([[d_i[token][user] >= 0 for user in Users] for token in Tokens])),
        And(flatten([r_i[token] >= 0 for token in Tokens])),
        # def of credits supply
        And(flatten(
                [
                    C_i[token] == sum(flatten(list([c_i[token][user]] for user in Users)))   
                    for token in Tokens
                ]
            )),
        # def of debts supply
        And(flatten(
                [
                    D_i[token] == sum(flatten(list([d_i[token][user]] for user in Users)))   
                    for token in Tokens
                ]
            )),
        And(flatten([p_i[token] > 0 for token in Tokens])),
        # def of exchange rate
        And(flatten(
                [
                    X_i[token] == 
                        If(
                            C_i[token] != 0,
                            (r_i[token]+D_i[token]) / C_i[token],
                            1)
                    for token in Tokens
                ]
            )),
        # def of wallet value
        And(flatten(
                    [
                        Ww_i[user] == sum(flatten(list([w_i[token][user]] for token in Tokens)))   
                        for user in Users
                    ]
            )),
        # def of credits value
        And(flatten(
                    [
                        Wc_i[user] == sum(flatten(list([c_i[token][user]] for token in Tokens)))   
                        for user in Users
                    ]
            )),
        # def of debts value
        And(flatten(
                    [
                        Wd_i[user] == sum(flatten(list([d_i[token][user]] for token in Tokens)))   
                        for user in Users
                    ]
            )),
        # def of net worth
        And(flatten(
                    [
                        W_i[user] == Ww_i[user] + Wc_i[user] - Wd_i[user]    
                        for user in Users
                    ]
            )),

        # def of collateralization
        And(flatten(
                [
                    Coll_i[user] == 
                        If(
                            Wd_i[user] > 0,
                            Wc_i[user] / Wd_i[user],
                            INFTY
                        )
                    for user in Users
                ]
            )),
        # def of health factor
        And(flatten(
            [
                Health_i[user] ==  Coll_i[user]*Tliq
                for user in Users
            ]
            )),
        And(flatten([I_i[token] > 0 for token in Tokens])),

        # def. of utilization
        And(flatten(
                [
                    U_i[token] ==  
                        If(
                            D_i[token] == 0,
                            0,
                            D_i[token] / (r_i[token] + D_i[token])
                        )
                    for token in Tokens
                ]
            )), 
        # def. of utilization interest rate
        And(flatten(
                [
                    I_i[token] == alfa * U_i[token] + beta
                    for token in Tokens
                ]
            )),

        )

def initial_conditions():
    return And(
        And(flatten([r[0][token] == 0 for token in Tokens])),
        And(flatten([[c[0][token][user] == 0 for user in Users] for token in Tokens])),
        And(flatten([[d[0][token][user] == 0 for user in Users] for token in Tokens]))
    )

list_state_variables = [ w, r, c, d, C, D, p, X, Ww, Wc, Wd, W, Coll, Health, I, U]


state_variables = [
    {
    'w':w[state],
    'r':r[state],
    'c':c[state],
    'd':d[state],
    'C':C[state],
    'D':D[state],
    'p':p[state],
    'X':X[state],
    'Ww':Ww[state],
    'Wc':Wc[state],
    'Wd':Wd[state],
    'W':W[state],
    'Coll':Coll[state],
    'Health':Health[state],
    'I':I[state]
    }
    for state in States
]

#pprint.pprint(state_variables)


# Transition variables

# Actions
Action = Datatype('Action')
Action.declare('dep')
Action.declare('bor')
Action.declare('rep')
Action.declare('rdm')
Action.declare('liq')
Action.declare('swp')
Action.declare('int')
Action.declare('px')
Action = Action.create()
action = [Const("action_s%s" % (i), Action) for i in States]


# sender of tx
tx_user = [Real("tx_user_s%s" % (i)) for i in States[:-1]]

# sender must be in Users
s.add((And([
                    Or([tx_user[state] == user for user in Users]) 
                   for state in States[:-1]])))

# v param of tx (used also as delta in px)
tx_v = [Real("tx_v_s%s" % (i)) for i in States[:-1]]

# T param of tx
tx_tok = [Real("tx_tok_s%s" % (i)) for i in States[:-1]]

# tx_tok must be in Tokens
s.add((And([
                    Or([tx_tok[state] == token for token in Tokens]) 
                   for state in States[:-1]])))


# user liquidated (param of tx for liq)
tx_liquser = [Real("tx_liquser_s%s" % (i)) for i in States[:-1]]
s.add((And([
                    Or([tx_liquser[state] == user for user in Users]) 
                   for state in States[:-1]])))

# 2nd token used in liq and swp
tx_tok2 = [Real("tx_tok2_s%s" % (i)) for i in States[:-1]]

# tx_liqcr must be in Tokens
s.add((And([
                    Or([tx_tok2[state] == token for token in Tokens]) 
                   for state in States[:-1]])))


# True iff transaction is not enabled
revert = [Bool("revert_s%s" % (i)) for i in States[:-1]]

list_trans_variables = [
    action, tx_user, tx_v, tx_tok, tx_liquser, tx_tok2, revert,
]

transition_variables = [
    {
    'action':action[state],
    'tx_user':tx_user[state],
    'tx_v':tx_v[state],
    'tx_tok':tx_tok[state],
    'tx_liquser':tx_liquser[state],
    'tx_tok2':tx_tok2[state],
    'revert':revert[state],
    }
    for state in States[:-1]
]


def same_state_tok(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next,
                   tok):
    return And(
        And([
            w_next[tok][user] == w_now[tok][user] 
            for user in Users]),
        And([
            c_next[tok][user] == c_now[tok][user] 
            for user in Users]),
        And([
            d_next[tok][user] == d_now[tok][user] 
            for user in Users]),
        r_next[tok] == r_now[tok],
        p_next[tok] == p_now[tok] 
    )

def same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next):
    return And([same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     token) for token in Tokens])


def deposit(
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now, user == tx_user_now), 
            w_now[tok][user] >= tx_v_now, 
        ) 
        for tok in Tokens for user in Users]),
        tx_v_now > 0
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([If(tok == tx_tok_now, 
                    And(
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok] + tx_v_now, 
                        And([If( user == tx_user_now,
                            And(
                                w_next[tok][user] ==  w_now[tok][user] - tx_v_now, 
                                c_next[tok][user] ==  c_now[tok][user] + tx_v_now/X_now[tok], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )) for user in Users])),
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok)
                    )
                for tok in Tokens ]),
        )
    ))

def redeem(        
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,

    ):
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now, user == tx_user_now),
            And( 
                c_now[tok][user] >= tx_v_now,
                r_now[tok] >= tx_v_now*X_now[tok],
                Health_next[user] >= 1
            ), 
        ) 
        for tok in Tokens for user in Users]),
        tx_v_now > 0
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([If(tok == tx_tok_now, 
                    And(
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok] - tx_v_now*X_now[tok], 
                        And([If( user == tx_user_now,
                            And(
                                w_next[tok][user] ==  w_now[tok][user] + tx_v_now*X_now[tok], 
                                c_next[tok][user] ==  c_now[tok][user] - tx_v_now, 
                                d_next[tok][user] ==  d_now[tok][user], 
                            ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )) for user in Users])),
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok)
                    )
                for tok in Tokens ]),
        )
    ))


def borrow(
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now, user == tx_user_now), 
            And(
                r_now[tok] >= tx_v_now,
                Health_next[user] >= 1,
                ), 
        ) 
        for tok in Tokens for user in Users]),
        tx_v_now > 0
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([If(tok == tx_tok_now, 
                    And(
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok] - tx_v_now, 
                        And([If( user == tx_user_now,
                            And(
                                w_next[tok][user] ==  w_now[tok][user] + tx_v_now, 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user] + tx_v_now, 
                            ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )) for user in Users])),
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok)
                    )
                for tok in Tokens ]),
        )
    ))



def repay(        
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now, user == tx_user_now), 
            And(
                w_now[tok][user] >= tx_v_now,
                d_now[tok][user] >= tx_v_now,    
                ), 
        ) 
        for tok in Tokens for user in Users]),
        tx_v_now > 0
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([If(tok == tx_tok_now, 
                    And(
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok] + tx_v_now, 
                        And([If( user == tx_user_now,
                            And(
                                w_next[tok][user] ==  w_now[tok][user] - tx_v_now, 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user] - tx_v_now, 
                            ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )) for user in Users])),
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok)
                    )
                for tok in Tokens ]),
        )
    ))



def liquidate(
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):
    #vc1 = (tx_v_now / X_now[tok_liqed] * p_now[tok] / p_now[tok_liqed] * Rliq) 
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now, tok_liqed == tx_tok2_now, user == tx_user_now, user_liqed==tx_liquser_now),
            And( 
                w_now[tok][user] >= tx_v_now,
                d_now[tok][user_liqed] >= tx_v_now,
                c_now[tok_liqed][user_liqed] >= (tx_v_now / X_now[tok_liqed] * p_now[tok] / p_now[tok_liqed] * Rliq),
                user != user_liqed,
                Health_now[user_liqed] < 1,
                Health_next[user_liqed] <= 1,
            ), 
        ) 
        for tok in Tokens for tok_liqed in Tokens for user in Users for user_liqed in Users]),
        tx_v_now > 0
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([If(And(tok == tx_tok_now, tok_liqed == tx_tok2_now, tok == tok_liqed), # tok = T0 = T1
                    And(
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok] + tx_v_now, 
                        And([If( user == tx_user_now,    # user == A
                            And(
                                w_next[tok][user] ==  w_now[tok][user] - tx_v_now, 
                                c_next[tok][user] ==  c_now[tok][user] + (tx_v_now / X_now[tok] * p_now[tok] / p_now[tok] * Rliq), 
                                d_next[tok][user] ==  d_now[tok][user], 
                            ),
                            If( user == tx_liquser_now, # user == B
                                And(
                                    w_next[tok][user] ==  w_now[tok][user], 
                                    c_next[tok][user] ==  c_now[tok][user] - (tx_v_now / X_now[tok] * p_now[tok] / p_now[tok] * Rliq), 
                                    d_next[tok][user] ==  d_now[tok][user] - tx_v_now, 
                                ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )
                            )) for user in Users])),
                    If(And(tok == tx_tok_now, tok_liqed == tx_tok2_now),    
                       And(                         # T0 
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok] + tx_v_now, 
                        And([If( user == tx_user_now,    # user == A
                            And(
                                w_next[tok][user] ==  w_now[tok][user] - tx_v_now, 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            ),
                            If( user == tx_liquser_now, # user == B
                                And(
                                    w_next[tok][user] ==  w_now[tok][user], 
                                    c_next[tok][user] ==  c_now[tok][user], 
                                    d_next[tok][user] ==  d_now[tok][user] - tx_v_now, 
                                ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )
                            )) for user in Users]),
                          And(          #  T1
                        p_next[tok_liqed] == p_now[tok_liqed],
                        r_next[tok_liqed] == r_now[tok_liqed], 
                        And([If( user == tx_user_now,    # user == A
                            And(
                                w_next[tok_liqed][user] ==  w_now[tok_liqed][user], 
                                c_next[tok_liqed][user] ==  c_now[tok_liqed][user] + (tx_v_now / X_now[tok] * p_now[tok] / p_now[tok_liqed] * Rliq), 
                                d_next[tok_liqed][user] ==  d_now[tok_liqed][user], 
                            ),
                            If( user == tx_liquser_now, # user == B
                                And(
                                    w_next[tok_liqed][user] ==  w_now[tok_liqed][user], 
                                    c_next[tok_liqed][user] ==  c_now[tok_liqed][user] - (tx_v_now / X_now[tok] * p_now[tok] / p_now[tok_liqed] * Rliq), 
                                    d_next[tok_liqed][user] ==  d_now[tok_liqed][user], 
                                ),
                            And(
                                w_next[tok_liqed][user] ==  w_now[tok_liqed][user], 
                                c_next[tok_liqed][user] ==  c_now[tok_liqed][user], 
                                d_next[tok_liqed][user] ==  d_now[tok_liqed][user], 
                            )
                            )) for user in Users])), 
                       ),                      
                    If(And(tok != tx_tok_now, tok_liqed != tx_tok2_now),  # != T0, != T1
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok),
                    True
                    )
                    ))
                for tok in Tokens for tok_liqed in Tokens]),
        )
    ))




def swap(
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):  
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now, tok2 == tx_tok2_now, user == tx_user_now),
            And( 
                tok != tok2,
                w_now[tok][user] >= tx_v_now,
            ), 
        ) 
        for tok in Tokens for tok2 in Tokens for user in Users]),
        tx_v_now > 0
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([
                    If(And(tok == tx_tok_now, tok2 == tx_tok2_now),    
                       And(                         # T0 
                        p_next[tok] == p_now[tok],
                        r_next[tok] == r_now[tok], 
                        And([
                            If( user == tx_user_now, 
                                And(
                                    w_next[tok][user] ==  w_now[tok][user] - tx_v_now, 
                                    c_next[tok][user] ==  c_now[tok][user], 
                                    d_next[tok][user] ==  d_now[tok][user], 
                                ),
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            )
                            ) for user in Users]),
                          And(          #  T1
                        p_next[tok2] == p_now[tok2],
                        r_next[tok2] == r_now[tok2], 
                        And([
                            If( user == tx_user_now, 
                                And(
                                    w_next[tok2][user] ==  w_now[tok2][user] +  tx_v_now*p_now[tok]/p_now[tok2] , 
                                    c_next[tok2][user] ==  c_now[tok2][user], 
                                    d_next[tok2][user] ==  d_now[tok2][user], 
                                ),
                            And(
                                w_next[tok2][user] ==  w_now[tok2][user], 
                                c_next[tok2][user] ==  c_now[tok2][user], 
                                d_next[tok2][user] ==  d_now[tok2][user], 
                            )
                            ) for user in Users])), 
                       ),                      
                    If(And(tok != tx_tok_now, tok2 != tx_tok2_now),  # != T0, != T1
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok),
                    True
                    )
                    )
                for tok in Tokens for tok2 in Tokens]),
        )
    ))


def priceupdate(
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):
    conditions = And(
        And([Implies(
            And(tok == tx_tok_now), 
            tx_v_now != 0,
            p_now[tok] + tx_v_now > 0
        ) 
        for tok in Tokens]),
    )
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And(
            And([If(tok == tx_tok_now, 
                    And(
                        p_next[tok] == p_now[tok] +  tx_v_now,
                        r_next[tok] == r_now[tok], 
                        And([
                            And(
                                w_next[tok][user] ==  w_now[tok][user], 
                                c_next[tok][user] ==  c_now[tok][user], 
                                d_next[tok][user] ==  d_now[tok][user], 
                            ) for user in Users])),
                    same_state_tok(w_now, r_now, c_now, d_now, p_now,
                     w_next, r_next, c_next, d_next, p_next,
                     tok)
                    )
                for tok in Tokens ]),
        )
    ))


def intaccrual(
        w_now, r_now, c_now, d_now, C_now, D_now, p_now, X_now, Ww_now, Wc_now, Wd_now, W_now, Coll_now, Health_now, I_now, U_now,
        w_next, r_next, c_next, d_next, C_next, D_next, p_next, X_next, Ww_next, Wc_next, Wd_next, W_next, Coll_next, Health_next, I_next, U_next,
        action_now, tx_user_now, tx_v_now, tx_tok_now, tx_liquser_now, tx_tok2_now, revert_now,
    ):
    conditions = True
    return And(
        revert_now == Not(conditions),
        If(
        revert_now,
        same_state(w_now, r_now, c_now, d_now, p_now,
                   w_next, r_next, c_next, d_next, p_next),
        And([
            And(
            p_next[tok] == p_now[tok],
            r_next[tok] == r_now[tok], 
            w_next[tok][user] ==  w_now[tok][user], 
            c_next[tok][user] ==  c_now[tok][user], 
            d_next[tok][user] ==  d_now[tok][user] + d_now[tok][user]*I_now[tok]) 
            for user in Users for tok in Tokens
        ]
        )
    ))



s.add(initial_conditions())

w_nx1 = [[Real("w_nx1_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
r_nx1 = [Real("r_nx1_t%s" % (token)) for token in Tokens]
c_nx1 = [[Real("c_nx1_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
d_nx1 = [[Real("d_nx1_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
C_nx1 = [Real("C_nx1_t%s" % (token)) for token in Tokens]
D_nx1 = [Real("D_nx1_t%s" % (token)) for token in Tokens]
p_nx1 = [Real("p_nx1_t%s" % (token)) for token in Tokens]
X_nx1 = [Real("X_nx1_t%s" % (token)) for token in Tokens]
Ww_nx1 = [Real("Ww_nx1_u%s" % (user)) for user in Users]
Wc_nx1 = [Real("Wc_nx1_u%s" % (user)) for user in Users]
Wd_nx1 = [Real("Wd_nx1_u%s" % (user)) for user in Users]
W_nx1 = [Real("W_nx1_u%s" % (user)) for user in Users]
Coll_nx1 = [Real("Coll_nx1_u%s" % (user)) for user in Users]
Health_nx1 = [Real("Health_nx1_u%s" % (user)) for user in Users]
I_nx1 = [Real("I_nx1_t%s" % (token)) for token in Tokens]
U_nx1 = [Real("U_nx1_t%s" % (token)) for token in Tokens]


w_nx11 = [[Real("w_nx11_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
r_nx11 = [Real("r_nx11_t%s" % (token)) for token in Tokens]
c_nx11 = [[Real("c_nx11_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
d_nx11 = [[Real("d_nx11_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
C_nx11 = [Real("C_nx11_t%s" % (token)) for token in Tokens]
D_nx11 = [Real("D_nx11_t%s" % (token)) for token in Tokens]
p_nx11 = [Real("p_nx11_t%s" % (token)) for token in Tokens]
X_nx11 = [Real("X_nx11_t%s" % (token)) for token in Tokens]
Ww_nx11 = [Real("Ww_nx11_u%s" % (user)) for user in Users]
Wc_nx11 = [Real("Wc_nx11_u%s" % (user)) for user in Users]
Wd_nx11 = [Real("Wd_nx11_u%s" % (user)) for user in Users]
W_nx11 = [Real("W_nx11_u%s" % (user)) for user in Users]
Coll_nx11 = [Real("Coll_nx11_u%s" % (user)) for user in Users]
Health_nx11 = [Real("Health_nx11_u%s" % (user)) for user in Users]
I_nx11 = [Real("I_nx11_t%s" % (token)) for token in Tokens]
U_nx11 = [Real("U_nx11_t%s" % (token)) for token in Tokens]


w_nx2 = [[Real("w_nx2_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
r_nx2 = [Real("r_nx2_t%s" % (token)) for token in Tokens]
c_nx2 = [[Real("c_nx2_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
d_nx2 = [[Real("d_nx2_t%s_u%s" % (token, user)) for user in Users] for token in Tokens]
C_nx2 = [Real("C_nx2_t%s" % (token)) for token in Tokens]
D_nx2 = [Real("D_nx2_t%s" % (token)) for token in Tokens]
p_nx2 = [Real("p_nx2_t%s" % (token)) for token in Tokens]
X_nx2 = [Real("X_nx2_t%s" % (token)) for token in Tokens]
Ww_nx2 = [Real("Ww_nx2_u%s" % (user)) for user in Users]
Wc_nx2 = [Real("Wc_nx2_u%s" % (user)) for user in Users]
Wd_nx2 = [Real("Wd_nx2_u%s" % (user)) for user in Users]
W_nx2 = [Real("W_nx2_u%s" % (user)) for user in Users]
Coll_nx2 = [Real("Coll_nx2_u%s" % (user)) for user in Users]
Health_nx2 = [Real("Health_nx2_u%s" % (user)) for user in Users]
I_nx2 = [Real("I_nx2_t%s" % (token)) for token in Tokens]
U_nx2 = [Real("U_nx2_t%s" % (token)) for token in Tokens]

action_nx1, tx_user_nx1, tx_v_nx1, tx_tok_nx1, tx_liquser_nx1, tx_tok2_nx1 = Reals('action_nx1 tx_user_nx1 tx_v_nx1 tx_tok_nx1 tx_liquser_nx1 tx_tok2_nx1')
action_nx11, tx_user_nx11, tx_v_nx11, tx_tok_nx11, tx_liquser_nx11, tx_tok2_nx11 = Reals('action_nx11 tx_user_nx11 tx_v_nx11 tx_tok_nx11 tx_liquser_nx11 tx_tok2_nx11')
action_nx2, tx_user_nx2, tx_v_nx2, tx_tok_nx2, tx_liquser_nx2, tx_tok2_nx2 = Reals('action_nx2 tx_user_nx2 tx_v_nx2 tx_tok_nx2 tx_liquser_nx2 tx_tok2_nx2')
revert_nx1, revert_nx11, revert_nx2 = Reals('revert_nx1 revert_nx11 revert_nx2')

s.add(state_conditions(w_nx1, r_nx1, c_nx1, d_nx1, C_nx1, D_nx1, p_nx1, X_nx1, Ww_nx1, Wc_nx1, Wd_nx1, W_nx1, Coll_nx1, Health_nx1, I_nx1, U_nx1))
s.add(state_conditions(w_nx11, r_nx11, c_nx11, d_nx11, C_nx11, D_nx11, p_nx11, X_nx11, Ww_nx11, Wc_nx11, Wd_nx11, W_nx11, Coll_nx11, Health_nx11, I_nx11, U_nx11))
s.add(state_conditions(w_nx2, r_nx2, c_nx2, d_nx2, C_nx2, D_nx2, p_nx2, X_nx2, Ww_nx2, Wc_nx2, Wd_nx2, W_nx2, Coll_nx2, Health_nx2, I_nx2, U_nx2))



action_nx1 = Const("action_nx1", Action)
tx_user_nx1 = Real("tx_user_nx1")
s.add((And(Or([tx_user_nx1 == user for user in Users]))))
tx_v_nx1 = Real("tx_v_nx1")
tx_tok_nx1 = Real("tx_tok_nx1")
s.add((And(Or([tx_tok_nx1 == token for token in Tokens]))))
tx_liquser_nx1 = Real("tx_liquser_nx1")
s.add((And(Or([tx_liquser_nx1 == user for user in Users]) )))
tx_tok2_nx1 = Real("tx_tok2_nx1")
s.add((And(Or([tx_tok2_nx1 == token for token in Tokens]))))
revert_nx1 = Bool("revert_nx1")



action_nx11 = Const("action_nx11", Action)
tx_user_nx11 = Real("tx_user_nx11")
s.add((And(Or([tx_user_nx11 == user for user in Users]))))
tx_v_nx11 = Real("tx_v_nx11")
tx_tok_nx11 = Real("tx_tok_nx11")
s.add((And(Or([tx_tok_nx11 == token for token in Tokens]))))
tx_liquser_nx11 = Real("tx_liquser_nx11")
s.add((And(Or([tx_liquser_nx11 == user for user in Users]) )))
tx_tok2_nx11 = Real("tx_tok2_nx11")
s.add((And(Or([tx_tok2_nx11 == token for token in Tokens]))))
revert_nx11 = Bool("revert_nx11")


action_nx2 = Const("action_nx2", Action)
tx_user_nx2 = Real("tx_user_nx2")
s.add((And(Or([tx_user_nx2 == user for user in Users]))))
tx_v_nx2 = Real("tx_v_nx2")
tx_tok_nx2 = Real("tx_tok_nx2")
s.add((And(Or([tx_tok_nx2 == token for token in Tokens]))))
tx_liquser_nx2 = Real("tx_liquser_nx2")
s.add((And(Or([tx_liquser_nx2 == user for user in Users]) )))
tx_tok2_nx2 = Real("tx_tok2_nx2")
s.add((And(Or([tx_tok2_nx2 == token for token in Tokens]))))
revert_nx2 = Bool("revert_nx2")

def step_trans(state_vars, next_state_vars, trans_vars):
    next_state = Or(
        And(action[i] == Action.dep , 
            deposit(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.bor , 
            borrow(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.rep , 
            repay(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.rdm , 
            redeem(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.liq , 
            liquidate(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.swp , 
            swap(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.px , 
            priceupdate(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        And(action[i] == Action.int , 
            intaccrual(*state_vars, 
                    *next_state_vars, 
                    *trans_vars)),
        )
    return next_state


def lem51(action, greater, i):
    if action == 'dep' and greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 0,
            beta == 1,
            c[i][0][0] == 0,
            C[i][0] == 1,
            d[i][0][0] == 1,
            D[i][0] == 1,
            r[i][0] == 0,
        )        
    elif action == 'dep' and not greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 1,
            beta == 1/8,
            c[i][0][0] == 1,
            C[i][0] == 2,
            d[i][0][0] == 1/32,
            D[i][0] == 1,
            r[i][0] == 1,
        ) 
    elif action == 'bor' and greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 3,
            beta == 1/16,
            c[i][0][0] == 2,
            C[i][0] == 3,
            d[i][0][0] == 1/32,
            D[i][0] == 1,
            r[i][0] == 2,
        )        
    elif action == 'bor' and not greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 4,
            beta == 1,
            c[i][0][0] == 1/2,
            C[i][0] == 1,
            d[i][0][0] == 1/4,
            D[i][0] == 1/2,
            r[i][0] == 1/2,
        )     
    elif action == 'rep' and greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 0,
            beta == 1,
            C[i][0] == 1,
            c[i][0][0] == 0,
            d[i][0][0] == 1,
            D[i][0] == 1,
            r[i][0] == 0,
        )        
    elif action == 'rep' and not greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 1,
            beta == 1/2,
            C[i][0] == 1,
            c[i][0][0] == 0,
            d[i][0][0] == 3/4,
            D[i][0] == 1,
            r[i][0] == 0,
        )   
    elif action == 'rdm' and greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 1,
            beta == 1,
            c[i][0][0] == 2,
            C[i][0] == 2,
            d[i][0][0] == 2/5,
            D[i][0] == 1,
            r[i][0] == 1,
        )        
    elif action == 'rdm' and not greater:
        return And(
            And([p[j][tok]==1 for tok in Tokens for j in range(i)]),
            alfa == 0,
            beta == 2,
            c[i][0][0] == 1,
            C[i][0] == 1,
            d[i][0][0] == 0,
            D[i][0] == 0,
            r[i][0] == 1,
        )   

for i in States[:-1]:
    print(i)
    s.add(state_conditions(*[var[i] for var in list_state_variables]))
    s.add(state_conditions(*[var[i+1] for var in list_state_variables]))
    s.add(action[0]==Action.dep)
    s.add(action[1]==Action.dep)
    s.add(action[2]==Action.bor)
    s.add(action[3]==Action.bor)
    #s.add(action[4]==Action.dep)
    #s.add(action[5]==Action.dep)
    s.add(Or(action[i] == Action.dep, action[i] == Action.bor))
    #s.add(Or(action[i] == Action.dep, action[i] == Action.bor, action[i] == Action.int))
    #s.add(And(action[i] != Action.int, action[i] != Action.px, action[i] != Action.liq,  action[i] != Action.swp))
    #s.add(And(action[i] != Action.px, action[i] != Action.liq,  action[i] != Action.swp))

    next_state = step_trans([var[i] for var in list_state_variables], 
                    [var[i+1] for var in list_state_variables], 
                    [var[i] for var in list_trans_variables])
    s.add(next_state)

    # Property to verify
    #prop = c[i][1][1]==2
    #prop = d[i][1][1]==2
    #prop = And(d[i][1][1]==2, D[i][1] <= 3)
    #prop = And(d[i][1][1]==2, D[i][1] <= 1)
    #prop = C[i][1] > r[i][1]+D[i][1] # Eq 3.1

    #prop = (action[i]== Action.dep, W[i+1][1] != W[i][1])

    """
    prop =  And(
            #alfa == 0,
            state_conditions(w_nx1, r_nx1, c_nx1, d_nx1, C_nx1, D_nx1, p_nx1, X_nx1, Ww_nx1, Wc_nx1, Wd_nx1, W_nx1, Coll_nx1, Health_nx1, I_nx1, U_nx1),
            state_conditions(w_nx11, r_nx11, c_nx11, d_nx11, C_nx11, D_nx11, p_nx11, X_nx11, Ww_nx11, Wc_nx11, Wd_nx11, W_nx11, Coll_nx11, Health_nx11, 
            I_nx11, U_nx11),
            state_conditions(w_nx2, r_nx2, c_nx2, d_nx2, C_nx2, D_nx2, p_nx2, X_nx2, Ww_nx2, Wc_nx2, Wd_nx2, W_nx2, Coll_nx2, Health_nx2, I_nx2, U_nx2),
            action_nx1 == Action.dep,
            c[i][0][0] > 0,
            #W_nx1[1] == -1,
            #Wd_nx1[1] == -1,
            #Wc_nx1[1] == -1,
            #Wc[1] == -1,
            #Ww_nx1[1] == 0,
            #W_nx1[1] != W[i][1],
            action_nx11 == Action.int,
            action_nx2 == Action.int,
            step_trans([var[i] for var in list_state_variables], 
                [w_nx1, r_nx1, c_nx1, d_nx1, C_nx1, D_nx1, p_nx1, X_nx1, Ww_nx1, Wc_nx1, Wd_nx1, W_nx1, Coll_nx1, Health_nx1, I_nx1, U_nx1],
                [action_nx1, tx_user_nx1, tx_v_nx1, tx_tok_nx1, tx_liquser_nx1, tx_tok2_nx1, revert_nx1]),
            step_trans([w_nx1, r_nx1, c_nx1, d_nx1, C_nx1, D_nx1, p_nx1, X_nx1, Ww_nx1, Wc_nx1, Wd_nx1, W_nx1, Coll_nx1, Health_nx1, I_nx1, U_nx1], 
                [w_nx11, r_nx11, c_nx11, d_nx11, C_nx11, D_nx11, p_nx11, X_nx11, Ww_nx11, Wc_nx11, Wd_nx11, W_nx11, Coll_nx11, Health_nx11, I_nx11, U_nx11], 
                [action_nx11, tx_user_nx11, tx_v_nx11, tx_tok_nx11, tx_liquser_nx11, tx_tok2_nx11, revert_nx11]),
            step_trans([var[i] for var in list_state_variables],
                [w_nx2, r_nx2, c_nx2, d_nx2, C_nx2, D_nx2, p_nx2, X_nx2, Ww_nx2, Wc_nx2, Wd_nx2, W_nx2, Coll_nx2, Health_nx2, I_nx2, U_nx2], 
                [action_nx2, tx_user_nx2, tx_v_nx2, tx_tok_nx2, tx_liquser_nx2, tx_tok2_nx2, revert_nx2]),        
            W_nx11[0] >  W_nx2[0]
            )
    """

    #prop = X[i][0] > 1
    #prop = C[i][0] == r[i][0]+D[i][0] # Eq 3.1
    #prop = d[i][0][0]==2

    #prop = And(action[0]==Action.dep, action[1]==Action.bor, action[i]==Action.int, X[i][0] > 1)
    #prop = And(d[i][0][0]==2, D[i][0] <= 3)


    s.add(Tliq==0.9)
    s.add(Rliq==1.1)
    act_lem = 'rdm'
    greater = True

    print(f"{act_lem=}")
    print(f"{greater=}")

    prop = lem51(act_lem,greater, i)    

    s2 = Solver()
    s2.add(s.assertions())
    s2.add(prop)
    text = s2.to_smt2()
    text = '(set-logic ALL)\n' + text + '\n(get-model)' 
    filename = f"lemma5.1/{act_lem}_{greater}.smt2"
    with open(filename, 'w') as my_file:
        my_file.write(text)

    res = s.check(prop)
    print(f"\nStep {i}: ",res)
    if res == sat:
        model = s.model()
        #print(model)
        d =  (sorted ([(d, model[d]) for d in model], key = lambda x: str(x[0])))
        #for el in d:
            #print(f"{el}\t->\t{d[el]}")
        #    print(f"{el}")
        print_model(model, i+1, state_variables[0], transition_variables[0])
        break

#print(s.assertions())
#for ass in s.assertions():
#    pprint.pprint(ass)

"""
regr_test = 1

if regr_test==1:    # dep
    s.check(And(
        c[3][1][1]==2,
        W[0][1]==2,
        #W[0][1]==0,
        W[0][0]==0,
        c[0][0][0]==0,
        ))
elif regr_test==2:  # dep
    s.check(c[3][1][1]==2)
elif regr_test==3:  # bor
    s.check(d[1][1][1]==2)
elif regr_test==4:
    s.check(And(
        c[3][1][1]==2,
        d[3][1][1]==2
                ))
"""

#m=s.model()
#print(m)


#print_model(m)
#print_model(model, Max_Steps, state_variables[0], transition_variables[0])