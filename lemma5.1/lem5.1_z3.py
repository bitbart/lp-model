import pprint	
from  z3 import *

c=Real('c') # Credits of user A
C=Real('C')	# Credit supply
d=Real('d')	# Debts of user A
D=Real('D')	# Debt supply
r=Real('r')	# LP reserves
X=Real('X')	# Exchange rate
v=Real('v')	# parameter v
a=Real('a')	# Int. rate parameter alpha
b=Real('b')	# Int. rate parameter beta
I=Real('I')	# Interest rate in Gamma0
Ii=Real('Ii')	# Interest rate in Gamma0'
f=Real('f')	# gain(Gamma0, X int) - gain(Gamma0, X)


gain1=Real('gain1')	# Gain of A in Gamma1
gain1i=Real('gain1i')	# Gain of A in Gamma1'

solv=Solver()

# no v
def conditions(c,C,d,D,a,b,r,I,gain1,X):
	return And(
		(c >= 0),
		(C >= 0),
		(d >= 0),
		(D >= 0),
		#(v > 0),
		(a >= 0),
		(b >= 0),
		(r >= 0),
		(I > 0),
		#(Ii > 0),
		(c <= C),
		(d <= D),
		(X == If(C == 0, 1, (r+D)/C)), # Def of Exchange rate
		(I == a*D/(r+D)+b),	# Def. of Interest rate
		(C <= r+D),	# Equation (3.1), following from Monotonicity of exchange rate
		(X >= 1),
		(C > 0),		# Hyp. in proof
		#solv.add(D > 0)		# Hyp. in proof (TODO aggiungere)	
		(gain1 == (c*D/C-d)*I)
	)

"""
solv.add(c >= 0)
solv.add(C >= 0)
solv.add(d >= 0)
solv.add(D >= 0)
solv.add(v > 0)
solv.add(a >= 0)
solv.add(b >= 0)
solv.add(r >= 0)

solv.add(I > 0)
solv.add(Ii > 0)


solv.add(c <= C)
solv.add(d <= D)

solv.add(X == If(C == 0, 1, (r+D)/C))


solv.add(I == a*D/(r+D)+b)	# Def. of Interest rate


solv.add(C <= r+D)	# Equation (3.1), following from Monotonicity of exchange rate
solv.add(X >= 1) 	# Corollary 3.5

#solv.add(r + D > 0)
#solv.add(r + D + v > 0)
#solv.add(C + v > 0)

solv.add(C > 0)		# Hyp. in proof
#solv.add(D > 0)		# Hyp. in proof (TODO aggiungere)

solv.add(gain1 == (c*D/C-d)*I)
solv.add(f == gain1i - gain1)
"""

Action = 'rdm'
print(f"{Action=}	")


def trans(c,C,d,D,v,a,b,r,I,Ii,X,f,gain1,gain1i, Action):
	if Action == 'dep':
		res=And(
			Ii == a*D/((r+v)+D)+b,
			(gain1i == ((c+v/X)*D/(C+v/X)-d)*Ii )
		)
	elif Action == 'bor':
		res=And(
			(Ii == a*(D+v)/((r-v)+(D+v))+b),
			(gain1i == (c*(D+v)/C-(d+v))*Ii),
			(r >= v)
		)
	elif Action == 'rep':
		res=And(
			(Ii == a*(D-v)/((r+v)+(D-v))+b),
			(gain1i == (c*(D-v)/C-(d-v))*Ii),
			(d >= v)
		)
	elif Action == 'rdm':
		res=And(
			(Ii == a*D/((r-v)+D)+b),
			(gain1i == ((c-v*X)*D/(C-v*X)-d)*Ii),
			(c >= v/X),
			(r >= v)
		)
	res = And(res,
		v>0,
		Ii > 0,
		(f == gain1i - gain1)
	)
	return res


"""
if Action == 'dep':
	solv.add(Ii == a*D/((r+v)+D)+b)
	solv.add(gain1i == ((c+v/X)*D/(C+v/X)-d)*Ii )
elif Action == 'bor':
	solv.add(Ii == a*(D+v)/((r-v)+(D+v))+b)
	solv.add(gain1i == (c*(D+v)/C-(d+v))*Ii)
	solv.add(r >= v)
elif Action == 'rep':
	solv.add(Ii == a*(D-v)/((r+v)+(D-v))+b)
	solv.add(gain1i == (c*(D-v)/C-(d-v))*Ii)
	solv.add(d >= v)
elif Action == 'rdm':
	solv.add(Ii == a*D/((r-v)+D)+b)
	solv.add(gain1i == ((c-v*X)*D/(C-v*X)-d)*Ii)
	solv.add(c >= v/X)
	solv.add(r >= v)
"""




#solv.add(Wi == (c*(D+v)/C-(d+v))*Ii)

#solv.add(a>0)
#solv.add(r>0)

#solv.add()
#solv.add(f>0)

solv.add(b>0)
#solv.add(a==0)

#solv.add((C*D**2*b + C*D*a*d + C*D*b*r - D**2*a*c - D**2*b*c - D*b*c*r)/(C*D + C*r)<0)


def check_and_print(prop):
	print(f"\n{prop=}")
	print(solv.check(prop))
	m= solv.model()
	pprint.pprint(sorted([(d, m[d]) for d in m], key = lambda x: str.lower(str(x[0]))))




cq=Real('cq') # Credits of user A
Cq=Real('Cq')	# Credit supply
dq=Real('dq')	# Debts of user A
Dq=Real('Dq')	# Debt supply
rq=Real('rq')	# LP reserves
Xq=Real('Xq')	# Exchange rate
vq=Real('vq')	# parameter v
aq=Real('aq')	# Int. rate parameter alpha
bq=Real('bq')	# Int. rate parameter beta
Iq=Real('Iq')	# Interest rate in Gamma0
Iiq=Real('Iiq')	# Interest rate in Gamma0'
fq=Real('fq')	# gain(Gamma0, X int) - gain(Gamma0, X)
prop=	ForAll(
		[c,C,d,D,a,b,r,I,gain1,X],
		Implies(
		conditions(c,C,d,D,a,b,r,I,gain1,X),
			Exists(
				[v, Ii, gain1i,f],
				And(
					trans(c,C,d,D,v,a,b,r,I,Ii,X,f,gain1,gain1i, Action),
					#c==0,
					#f<0
					)
				)))

#prop2 = ForAll([c,d],Exists([v], And(c<v,v<d)))
solv.add(conditions(c,C,d,D,a,b,r,I,gain1,X))
solv.add(trans(c,C,d,D,v,a,b,r,I,Ii,X, f,gain1,gain1i,Action))


solv.add(C-v*X != 0) # needed for rdm
solv.add(D+r<=C) # forces no Int
#solv.add(c == 0)		


#check_and_print(prop)

#solv.add(prop)

#solv.add(f>0)
text = "(set-logic NRA)" + solv.to_smt2() + "(get-model)"
#print(text)

with open("test.smt2", 'w') as my_file:
	my_file.write(text)



check_and_print(f>0)
check_and_print(f<0)
