###
# Author: Hai & Kevin
# CS 583
# Project 1
###
import re


##########
# Read input
##########
def get_input(in_file):
    transaction_db = []
    items = []

    file = open(in_file, "r")

    for line in file:
        transaction = re.findall(r"\d+", line)
        transaction = [ int(t) for t in transaction ]  # Convert strings into integers then create a list from them
        transaction_db += [transaction]
        items = set().union(items, transaction)

    file.close()
    return transaction_db, items


##########
# Read parameters
##########
def get_param(param_file):
    sdc = 0
    mis = {}
    cannot_be_together = []
    must_have = []

    file = open(param_file, "r")

    for line in file:

        if line[:3] == "MIS":
            l = re.match(r"MIS\((\d+)\)\s=\s(.*)", line)
            mis[int(l.group(1))] = float(l.group(2))
        
        if line[:3] == "SDC":
            l = re.match(r"SDC\s=\s(.*)", line)
            sdc = float(l.group(1))
        
        if line[:18] == "cannot_be_together":
            group = re.findall("{(\d+(,*\s*\d+)*)}", line)
            for g in group:
                items = re.findall(r"\d+", g[0])
                items = [int(i) for i in items]
                cannot_be_together.append(items)
        
        if line[:9] == "must-have":
            items = re.findall(r"\d+", line)
            items = [int(i) for i in items]
            for i in items:
                must_have.append([i])

    file.close()
    return sdc, mis, cannot_be_together, must_have

##########
# Count the occurences of a group of items in the transaction database
##########
def freq(transaction_db, itemgroup):
    count = 0
    for i in range(len(transaction_db)):
        if set(transaction_db[i]) & set(itemgroup) == set(itemgroup):    # Check if subset
            count += 1
    return count


##########
# Support
##########
def sup(transaction_db, itemgroup):
    return float(freq( transaction_db, itemgroup )) / len(transaction_db)


##########
# MSApriori algorithm
##########
def MSApriori(transaction_db, items, mis, sdc):
    F = [[]] * ( len(mis) + 1 )
    C = [[]] * ( len(mis) + 1 )
    count = {}
    tail_count = {}
    n = len(transaction_db)    # number of transaction

    # Sort the itemlist by its items' MIS
    M = sorted(items, key = lambda i : mis[i])

    # Init pass
    L = [ M[0] ]
    for j in range(1, len(M)):
        if freq( transaction_db, [M[j]] ) >= float(n) * mis[ M[0] ] :
            L.append( M[j] )
            count[ tuple( [M[j]] )] = freq(transaction_db, [M[j]] )

    # F1
    F[1] = []
    for item in L:
        if freq( transaction_db, [item] ) >= float(n) * mis[item]:
            F[1].append(item)
            count[ tuple( [item] )] = freq(transaction_db, [item] )

    # Generate candidates and count them
    k = 2
    while k <= n and len( F[k-1] ) > 0:
        F[k] = []

        if k == 2:
            C[2] = level2_candidate_gen(L, sdc)
            for c in C[2]:
                d = tuple(sorted(c, key = lambda i : mis[i]))
                count[d] = 0
                tail_count[d] = 0

        if k > 2:
            C[k] = MScandidate_gen(F[k-1], sdc)
            for c in C[k]:
                d = tuple(sorted(c, key = lambda i : mis[i]))
                count[d] = 0
                tail_count[d] = 0

        for t in transaction_db:
            for c in C[k]:

                if set(t) & set(c) == set(c):
                    d = tuple(sorted(c, key = lambda i : mis[i]))
                    count[d] += 1
                    tail_count[d] += 1

                if set(t) & set(c[1:]) == set(c[1:]):    # tail count
                    tail = tuple(c[1:])
                    if tail in tail_count.keys():
                        tail_count[tail] += 1
                    else:
                        tail_count[tail] = 1
        
        for c in C[k]:
            d = tuple(sorted(c, key = lambda i : mis[i]))
            if count[d] >= n * mis[ c[0] ]:
                F[k].append(c)

        k += 1

    # Remove duplications
    result = []
    for i in range(len(F)):
        for f in F[i]:
            if f not in result:
                if isinstance(f, int):
                    result.append([f])
                else:
                    result.append(f)

    return result, count, tail_count


##########
# Level 2 candidate-gen function
##########
def level2_candidate_gen(L, sdc):
    C2 = []    # initialize the set of candidates
    n = len(transaction_db)

    for i in range(0, len(L)-1):
        l = L[i]
        if freq( transaction_db, [l] ) >= float(n) * mis[l]:
            for j in range (i+1, len(L)):
                h = L[j]
            
                if freq( transaction_db, [h] ) >= float(n) * mis[l]:
                    if abs( sup(transaction_db, [h]) - sup(transaction_db, [l]) ) <= sdc:
                        C2.append([l, h])    # insert the candidate [l, h] into C2

    return C2

##########
# Candidate-gen function
##########
def MScandidate_gen(F_prev, sdc):
    Ck = []    # initialize the set of candidates

    for i in range(len(F_prev) - 1):
        f1 = F_prev[i]
        f1.sort()
        for j in range(i+1, len(F_prev)):    
            f2 = F_prev[j]
            f2.sort()

            # find all pairs of frequent itemsets that differ only in the last item
            if f1[:len(f1)-1] == f2[:len(f2)-1] and f1[-1] < f2[-1]:
                if abs( sup( transaction_db, [f1[-1]] ) - sup(  transaction_db, [f2[-1]] ) ) <= sdc:
                
                    c = f1.append(f2[-1])    # join the two itemsets f1 and f2
                    Ck.append(c)             # insert the candidate itemset c into Ck

                    for idx in range(1, len(c)+1):
                        s = c[:idx-1] + c[idx:]    # a (k-1)-subset of c
                        if c[1] in s or mis[c[2]] == mis[c[1]]:
                            if s not in F_prev:
                                Ck.remove(c)       # delete c from the set of candidates

    return Ck


##########
# Apply constraints: cannot_be_together and must_have
##########
def apply_constraints(F, cannot_be_together, must_have):
    idx = 0
    while idx < len(F):
        f = F[idx]
        flag = False

        for c in cannot_be_together:
            if flag:
                break
            
            # if c is a subset of group, remove this group from result
            if set(f) & set(c) == set(c):
                F.remove(f)
                flag = True
                idx -= 1

        flag = False

        for m in must_have:
            if len( set(f) & set(m) ) > 0:
                flag = True
                break

        # Group doesn't contain any must_have
        if not flag: 
            F.remove(f)
            idx -= 1

        idx += 1

    return F


##########
# Main
##########

# Read files for input and parameters
transaction_db, items = get_input("input-data.txt")
sdc, mis, cannot_be_together, must_have = get_param("parameter-file.txt")

# Run
F, count, tailCount = MSApriori(transaction_db, items, mis, sdc)

# Constraints
F = apply_constraints(F, cannot_be_together, must_have)
print F

# Generate a dictionary from F to be able to print output in the desired format
F_dict = {}
for f in F:
    if len(f) not in F_dict.keys():
        F_dict[len(f)] = []
    F_dict[len(f)].append(f)

# Start writing output
output = ""
f_out = open("output.txt", "w")

for i in range(len(mis)):
    if i in F_dict.keys():
        output += "Frequent " + str(i) + "-itemsets\n\n"
        
        for f in F_dict[i]:
            d = tuple(sorted(f, key = lambda i : mis[i]))
            output += "    " + str(count[d]) + " : " + "{" + ", ".join(map(str, f)) + "}\n"
            if i > 1:
                output += "Tailcount = " + str(tailCount[d]) + "\n"

        output += "\n    Total number of frequent " + str(i) + "-itemsets = " + str(len(F_dict[i])) + "\n\n\n"

f_out.write(output)
f_out.close()
