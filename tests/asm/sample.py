# lambdex: modopt
from lambdex import def_

n = 100
s = 0
adders = []
for i in range(n):
    adder = (lambda i: def_(lambda: [
        global_[s], 
        s < s + i
    ]))(i)
    adders.append(adder)

for adder in adders:
    adder()