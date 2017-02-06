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
        transaction = [ int(t) for t in transaction ]  # Convert strings into integers
        transaction_db += [transaction]
        items = set().union(items, transaction)

    file.close()
    return transaction_db, items


##########
# Count the occurences of a group of items in the transaction database
##########
def count(transaction_db, itemgroup):
    count = 0
    for i in range(len(transaction_db)):
        if set(transaction_db[i]) & set(itemgroup) == set(itemgroup):    # Check if subset
            count += 1
    return count


##########
# Support
##########
def sup(transaction_db, itemgroup):
    return float(count( transaction_db, itemgroup )) / len(transaction_db)


##########
# MSApriori algorithm
##########
def MSApriori(transaction_db, items, mis, sdc):
    output = []
    F = [[]] * ( len(mis) + 1 )
    C = [[]] * ( len(mis) + 1 )
    candidate_count = {}

    # Sort the itemlist by its items' MIS
    M = sorted(items, key = lambda i : mis[i])

    # Init pass
    L = [ M[0] ]
    for j in range(1, len(M)):
        if count( transaction_db, [M[j]] ) >= float(len(transaction_db)) * mis[ M[0] ] :
            L.append( M[j] )

    # F1
    F[1] = L
    for item in F[1]:
        if count( transaction_db, [item] ) < float(len(transaction_db)) * mis[item]:
            F[1].remove(item)

    # Generate candidates and count them
    k = 2
    while k <= len(mis) and len( F[k-1] ) > 0:
        if k == 2:
            C[2] = level2_candidate_gen(L, sdc)
            for candidate in C[2]:
                candidate_count[ tuple(candidate) ] = 0
        else:
            C[k] = MScandidate_gen(k, F[k-1], sdc)
            F[k] = []
            for candidate in C[k]:
                candidate_count[ tuple(candidate) ] = 0

        for t in transaction_db:
            for c in C[k]:

                if set(t) & set(c) == set(c):
                    candidate_count[ tuple(c) ] += 1

                if set(t) & set(c[1:]) == set(c[1:]):    # tail count
                    tail = tuple(c[1:])
                    if tail in candidate_count.keys():
                        candidate_count[tail] += 1
                    else:
                        candidate_count[tail] = 1
        
        for c in C[k]:
            if candidate_count[ tuple(c) ] >= len(transaction_db) * mis[ c[1] ]:
                F[k].append(c)

        k += 1

    # Remove duplications
    result = []
    for item in F[1]:
        if not item in result:
            result.append([item])

    for k in range(2, len(F)):
        for group in F[k]:
            if not group in result:
                result.append(group)

    return result


##########
# Level 2 candidate-gen function
##########
def level2_candidate_gen(L, sdc):
    C2 = []    # initialize the set of candidates
    for i in range(0, len(L)-1):
        l = L[i]
        if count( transaction_db, [l] ) >= float(len(transaction_db)) * mis[l]:
            for j in range (i+1, len(L)):
                h = L[j]
                if count( transaction_db, [h] ) >= float(len(transaction_db)) * mis[l] \
                and abs( sup(transaction_db, [h]) - sup(transaction_db, [l]) ) <= sdc:
                    C2.append([l, h])    # insert the candidate [l, h] into C2

    return C2

##########
# Candidate-gen function
##########
def MScandidate_gen(k, F_prev, sdc):
    Ck = []    # initialize the set of candidates

    for i in range(len(F_prev) - 1):
        f1 = F_prev[i]
        f1.sort()
        for j in range(i+1, len(F_prev)):    
            f2 = F_prev[j]
            f2.sort()

            # find all pairs of frequent itemsets that differ only in the last item
            if f1[:-2] == f2[:-2] and f1[-1] < f2[-1] and \
                abs( sup( transaction_db, [f1[-1]] ) - sup(  transaction_db, [f2[-1]] ) ) <= sdc:
                
                c = f1.append(f2[-1])    # join the two itemsets f1 and f2
                Ck.append(c)             # insert the candidate itemset c into Ck

                for idx in range(1, len(c)+1):
                    s = c[:idx-1] + c[idx:]    # a (k-1)-subset of c
                    if (c[1] in s) or (mis[c[2]] == mis[c[1]]):
                        if s not in F_prev:
                            Ck.remove(s)       # delete c from the set of candidates

    return Ck


##########
# Apply constraints: cannot_be_together and must_have
##########
def apply_constraints(F, cannot_be_together, must_have):
    for f in F:
        is_removed = False

        for c in cannot_be_together:
            if is_removed:
                break
            
            # if c is a subset of group, remove this group from result
            if set(f) & set(c) == set(c):
                F.remove(f)
                is_removed = True

        for m in must_have:
            if is_removed:
                break

            # if the intersection between m and group is empty, remove this group from result
            if not (set(f) & set(m)):
                F.remove(f)
                is_removed = True

    return F


##########
# Main
##########

# MIS
mis = {10:0.43, 20:0.30, 30:0.40, 40:0.40, 50:0.40, 60:0.30, 70:0.20, 80:0.20, 90:0.20, 100:0.10, 120:0.20, 140:0.15}

# Support difference constraint
sdc = 0.1

# Item constraints
cannot_be_together = [[20, 40], [70, 80]]
must_have = [[20], [40], [50]]

# Transactions
transaction_db, items = get_input("input-data.txt")

# Run
F = MSApriori(transaction_db, items, mis, sdc)
F = apply_constraints(F, cannot_be_together, must_have)
print F
