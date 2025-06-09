from z3 import *
import itertools, pprint
from collections.abc import Iterable

INFTY = 100000
USE_LIN_UTILIZATION_INT_RATE = True

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


Max_Steps = 4
States = range(Max_Steps)

# number of users
nUsers = 3
Users = range(nUsers)

# number of tokens
nTokens = 2
Tokens = range(nTokens)


# Liquidation threshold
Tliq = Real('TLiq')
s.add(Tliq > 0)

# Reward factor
Rliq = Real('RLiq')
s.add(Rliq > 0)

# wallets
w = [[[Real("w_s%s_t%s_u%s" % (state, token, user)) for user in Users] for token in Tokens] for state in States]
s.add(And(flatten([[[w[state][token][user] >= 0 for user in Users] for token in Tokens] for state in States])))

#print(w[4])

# reserves
r = [[Real("r_s%s_t%s" % (state, token)) for token in Tokens] for state in States]
s.add(And(flatten([[r[state][token] >= 0 for token in Tokens] for state in States])))
s.add(And(flatten([r[0][token] == 0 for token in Tokens])))

# credits map
c = [[[Real("c_s%s_t%s_u%s" % (state, token, user)) for user in Users] for token in Tokens] for state in States]
s.add(And(flatten([[[c[state][token][user] >= 0 for user in Users] for token in Tokens] for state in States])))
s.add(And(flatten([[c[0][token][user] == 0 for user in Users] for token in Tokens])))

# debts map
d = [[[Real("d_s%s_t%s_u%s" % (state, token, user)) for user in Users] for token in Tokens] for state in States]
s.add(And(flatten([[[d[state][token][user] >= 0 for user in Users] for token in Tokens] for state in States])))
s.add(And(flatten([[d[0][token][user] == 0 for user in Users] for token in Tokens])))

# credits supply
C = [[Real("C_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# def of credits supply
s.add( And(flatten(
        [
            [
                C[state][token] == sum(flatten(list([c[state][token][user]] for user in Users)))   
                for token in Tokens
            ]
        for state in States
        ]
      ))) 

print(sum(flatten(list([c[0][1][user]] for user in Users))))

# debts supply
D = [[Real("D_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# def of debt supply
s.add( And(flatten(
        [
            [
                D[state][token] == sum(flatten(list([d[state][token][user]] for user in Users)))   
                for token in Tokens
            ]
        for state in States
        ]
      ))) 

# price
p = [[Real("p_s%s_t%s" % (state, token)) for token in Tokens] for state in States]
s.add(And(flatten([[p[state][token] > 0 for token in Tokens] for state in States])))

# exchange rate
X = [[Real("X_s%s_t%s" % (state, token)) for token in Tokens] for state in States]

# def of exchange rate
s.add( And(flatten(
        [
            [
                X[state][token] == 
                    If(
                        C[state][token] != 0,
                        (r[state][token]+D[state][token]) / C[state][token],
                        1)
                for token in Tokens
            ]
        for state in States
        ]
      ))) 

# Wallet value
Ww = [[Real("Ww_s%s_u%s" % (state, user)) for user in Users] for state in States]


# def of wallet value
s.add( And(flatten(
        [
            [
                Ww[state][user] == sum(flatten(list([w[state][token][user]] for token in Tokens)))   
                for user in Users
            ]
        for state in States
        ]
      ))) 

# Credits value
Wc = [[Real("Wc_s%s_u%s" % (state, user)) for user in Users] for state in States]

# def of credits value
s.add( And(flatten(
        [
            [
                Wc[state][user] == sum(flatten(list([c[state][token][user]] for token in Tokens)))   
                for user in Users
            ]
        for state in States
        ]
      ))) 

# Debts value
Wd = [[Real("Wd_s%s_u%s" % (state, user)) for user in Users] for state in States]

# def of debt value
s.add( And(flatten(
        [
            [
                Wd[state][user] == sum(flatten(list([d[state][token][user]] for token in Tokens)))   
                for user in Users
            ]
        for state in States
        ]
      ))) 

# Net worth 
W = [[Real("W_s%s_u%s" % (state, user)) for user in Users] for state in States]

# def of net worth
s.add( And(flatten(
        [
            [
                W[state][user] == Ww[state][user] + Wc[state][user] - Wd[state][user]    
                for user in Users
            ]
        for state in States
        ]
      ))) 

# Collateralization 
Coll = [[Real("Coll_s%s_u%s" % (state, user)) for user in Users] for state in States]

# def of collateralization
s.add( And(flatten(
        [
            [
                Coll[state][user] == 
                    If(
                        Wd[state][user] > 0,
                        Wc[state][user] / Wd[state][user],
                        INFTY
                    )
                for user in Users
            ]
        for state in States
        ]
      ))) 

# Health factor 
Health = [[Real("Health_s%s_u%s" % (state, user)) for user in Users] for state in States]

# def of health factor
s.add( And(flatten(
        [
            [
                Health[state][user] ==  Coll[state][user]*Tliq
                for user in Users
            ]
        for state in States
        ]
      ))) 

# Interest rate
I = [[Real("I_s%s_t%s" % (state, token)) for token in Tokens] for state in States]
s.add(And(flatten([[I[state][token] > 0 for token in Tokens] for state in States])))

if USE_LIN_UTILIZATION_INT_RATE:
    # Param for linear utilization interest rate function
    alfa, beta = Reals('alfa beta') 
    # Utilization
    U = [[Real("U_s%s_t%s" % (state, token)) for token in Tokens] for state in States]
    # def. of utilization
    s.add( And(flatten(
            [
                [
                    U[state][token] ==  
                        If(
                            D[state][token] == 0,
                            0,
                            D[state][token] / (r[state][token] + D[state][token])
                        )
                    for token in Tokens
                ]
            for state in States
            ]
        ))) 
    # def. of utilization interest rate
    s.add( And(flatten(
            [
                [
                    I[state][token] == alfa * U[state][token] + beta
                    for token in Tokens
                ]
            for state in States
            ]
        ))) 

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

# v param of tx
tx_v = [Real("tx_v_s%s" % (i)) for i in States[:-1]]

# T param of tx
tx_tok = [Real("tx_tok_s%s" % (i)) for i in States[:-1]]

# True iff transaction is not enabled
revert = [Bool("revert_s%s" % (i)) for i in States[:-1]]

transition_variables = [
    {
    'tx_user':tx_user[state],
    'tx_v':tx_v[state],
    'tx_tok':tx_tok[state],
    'revert':revert[state],
    }
    for state in States[:-1]
]


def same_state(i, w, r, c, d, p):
    return And(
        And(flatten([[
            w[i+1][token][user] == w[i][token][user] 
            for user in Users]
            for token in Tokens])),
        And(flatten([[
            c[i+1][token][user] == c[i][token][user] 
            for user in Users]
            for token in Tokens])),
        And(flatten([[
            d[i+1][token][user] == d[i][token][user] 
            for user in Users]
            for token in Tokens])),
        And(flatten([
            r[i+1][token] == r[i][token] 
            for token in Tokens])),
        And(flatten([
            p[i+1][token] == p[i][token] 
            for token in Tokens]))
    )

def deposit(
        i,
        w, r, c, d, C, D, p, X, Health, I,
        tx_user, tx_v, tx_tok, revert
    ):
    conditions = And(
        And([Implies(
            And(tok == tx_tok[i], user == tx_user[i]), 
            w[i][tok][user] >= tx_v[i], 
        ) 
        for tok in Tokens for user in Users]),
        tx_v[i] > 0
    )
    #conditions = False
    return And(
        revert[i] == Not(conditions),
        If(
        revert[i],
        same_state(i, w, r, c, d, p),
        And(
            And([If(tok == tx_tok[i], 
                    And(
                        p[i+1][tok] == p[i][tok],
                        r[i+1][tok] ==  r[i][tok] + tx_v[i], 
                        And([If( user == tx_user[i],
                            And(
                                w[i+1][tok][user] ==  w[i][tok][user] - tx_v[i], 
                                c[i+1][tok][user] ==  c[i][tok][user] + tx_v[i]/X[i][tok], 
                                d[i+1][tok][user] ==  d[i][tok][user], 
                            ),
                            And(
                                w[i+1][tok][user] ==  w[i][tok][user], 
                                c[i+1][tok][user] ==  c[i][tok][user], 
                                d[i+1][tok][user] ==  d[i][tok][user], 
                            )) for user in Users])),
                    And(
                        p[i+1][tok] == p[i][tok],
                        r[i+1][tok] ==  r[i][tok], 
                        And([And(
                                w[i+1][tok][user] ==  w[i][tok][user], 
                                c[i+1][tok][user] ==  c[i][tok][user], 
                                d[i+1][tok][user] ==  d[i][tok][user], 
                            )
                            for user in Users])
                    )
                    )
                for tok in Tokens ]),
        )
    ))

#            And(flatten([p[i+1][token] == p[i][token] for token in Tokens]))

for i in States[:-1]:
    print(i)
    next_state = And(action[i] == Action.dep , 
            deposit(
            i,
            w, r, c, d, C, D, p, X, Health, I,
            tx_user, tx_v, tx_tok, revert ))
    s.add(next_state)


#print(s.assertions())
#for ass in s.assertions():
#    pprint.pprint(ass)

s.check(c[1][1][1]==2)

m=s.model()
print(m)

def print_model(m):
    m_d = {d: m[d] for d in m}
    for i in States:
        m_d_i = {}
        for key in m_d:
            if f"s{i}" in str(key):
                m_d_i[str(key)] = m_d[key]
        print("\n\n")
        pprint.pprint(m_d_i,sort_dicts=True)


def print_model2(m, state_variables, transition_variables):
    m_d = {d: m[d] for d in m}
    state_vars = list(state_variables.keys())
    trans_vars = list(transition_variables.keys())
    for v in state_vars+trans_vars:
        m_d_v = {}
        l_v = []
        for key in m_d:
            if f"{v}_" in str(key):
                m_d_v[str(key)] = m_d[key]
                l_v.append(m_d[key])
        #pprint.pprint(m_d_v,sort_dicts=True)
        print(str(v),'\t', '\t'.join([str(el) for el in l_v]))


def print_model3(m, state_variables, transition_variables):
    dont_print = ['Coll', 'Health', 'W','Ww', 'Wc', 'Wd', 'C', 'D']
    print(f"Tliq: {m[Tliq]}")
    print(f"Rliq: {m[Rliq]}")
    if USE_LIN_UTILIZATION_INT_RATE:
        print(f"alfa: {m[alfa]}")
        print(f"beta: {m[beta]}")
    m_d = {d: m[d] for d in m}
    state_vars = list(state_variables.keys())
    trans_vars = list(transition_variables.keys())
    for v in trans_vars + state_vars:
        if v in dont_print:
            continue
        print("\n",v[:6], end="\t")
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
                print(f'U{user}\t\t','\t'.join([str(m_d_v[el]) for el in keys if f"_u{user}" in str(el)]), end="\n\t")
        elif "_t" in first_key and "_u" not in first_key and not v in trans_vars :  # var only depends on token
            #print("var only depends on token")
            for token in Tokens:
                print(f'T{token}\t\t','\t'.join([str(m_d_v[el]) for el in keys if f"_t{token}" in str(el)]), end="\n\t")
        elif "_t" in first_key and "_u" in first_key  and not v in trans_vars:  # var depends on both token and user
            #print("var depends on both users and tokens")
            for token in Tokens:
                print(f'T{token}', end="")
                for user in Users:
                    print(f'\tU{user}\t','\t'.join([str(m_d_v[el]) for el in keys if f"_t{token}_u{user}" in str(el)]), end="\n\t")
        else:   
            print(f'\t\t','\t'.join([str(m_d_v[el]) for el in m_d_v.keys()]), end="\n\t")
                

def print_model4(m, state_variables, transition_variables):
    dont_print = ['Coll', 'Health', 'W','Ww', 'Wc', 'Wd', 'C', 'D']
    print(f"Tliq: {m[Tliq]}")
    print(f"Rliq: {m[Rliq]}")
    if USE_LIN_UTILIZATION_INT_RATE:
        print(f"alfa: {m[alfa]}")
        print(f"beta: {m[beta]}")
    m_d = {str(d): m[d] for d in m}
    state_vars = list(state_variables.keys())
    trans_vars = list(transition_variables.keys())
    for v in trans_vars + state_vars:
        if v in dont_print:
            continue
        print("\n",v[:6], end="\t")
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
                print(f'U{user}\t\t','\t'.join([str(m_d[f"{v}_s{state}_u{user}"]) for state in States]), end="\n\t")
        elif "_t" in first_key and "_u" not in first_key and not v in trans_vars :  # var only depends on token
            #print("var only depends on token")
            for token in Tokens:
                print(f'T{token}\t\t','\t'.join([str(m_d[f"{v}_s{state}_t{token}"]) for state in States]), end="\n\t")
        elif "_t" in first_key and "_u" in first_key  and not v in trans_vars:  # var depends on both token and user
            #print("var depends on both users and tokens")
            for token in Tokens:
                print(f'T{token}', end="")
                for user in Users:
                    print(f'\tU{user}\t','\t'.join([str(m_d[f"{v}_s{state}_t{token}_u{user}"]) for state in States]), end="\n\t")
        else:   
            print(f'\t\t','\t'.join([str(m_d[f"{v}_s{state}"]) for state in States[:-1]]), end="\n\t")
            #print(f'\t\t','\t'.join([str(m_d_v[el]) for el in m_d_v.keys()]), end="\n\t")
                
#print_model(m)
print_model4(m,state_variables[0], transition_variables[0])