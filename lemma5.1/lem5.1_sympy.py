from  sympy import *

c=Symbol('c') # Credits of user A
C=Symbol('C')	# Credit supply
d=Symbol('d')	# Debts of user A
D=Symbol('D')	# Debt supply
r=Symbol('r')	# LP reserves
X=Symbol('X')	# Exchange rate
v=Symbol('v')	# parameter v
a=Symbol('a')	# Int. rate parameter alpha
b=Symbol('b')	# Int. rate parameter beta
I = a*D/(r+D)+b	# Interest rate in Gamma0


# f	# gain(Gamma0, X int) - gain(Gamma0, X)
# Ii = ... # Interest rate in Gamma0' (defined by cases below)

C=0
c=0

Action = 'dep'
print(f"{Action=}	")

if Action == 'dep':
	Ii = a*D/((r+v)+D)+b
	f = ((c+v/X)*D/(C+v/X)-d)*Ii - (c*D/C-d)*I
elif Action == 'bor':
	Ii = a*(D+v)/((r-v)+(D+v))+b
	f = (c*(D+v)/C-(d+v))*Ii - (c*D/C-d)*I
elif Action == 'rep':
	Ii = a*(D-v)/((r+v)+(D-v))+b
	f = (c*(D-v)/C-(d-v))*Ii - (c*D/C-d)*I	
elif Action == 'rdm':
	Ii = a*D/((r-v)+D)+b
	f = ((c-v*X)*D/(C-v*X)-d)*Ii - (c*D/C-d)*I




show_diff = False

#print(f)
#print(p)

def print_subcases(dict_subs):
	if dict_subs == {}:
		print("\n\n\nGENERAL CASE")
		fsub = f
	else:
		print("\n\n\nSETTING ", ' , '.join([f"{el} -> {dict_subs[el]}" for el in dict_subs]), "\n")
		fsub = simplify(f.subs(dict_subs))
	print(fsub)
	print("Solve:\n",solve(fsub,v))
	print("Limit at 0:\n", simplify(limit(fsub,v,0)))
	if Action == 'dep':
		max_limit = oo
	if Action == 'bor':
		max_limit = r
	if Action == 'rep':
		max_limit = d
	if Action == 'rdm':
		max_limit = c
	print(f"Limit at max_limit ({max_limit}):\n", limit(fsub,v,max_limit))
	print("Singularities:\n",singularities(fsub,v))
	if show_diff:
		dfsub = diff(fsub,v)
		print("\tDeriv: ", dfsub)
		print("\tDeriv solve: ", solve(dfsub,v))


print_subcases({})
print_subcases({a:0})
print_subcases({b:0})
