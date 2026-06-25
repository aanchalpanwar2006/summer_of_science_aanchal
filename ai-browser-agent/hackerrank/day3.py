# Day 3: Intro to Conditional Statements
# Read N; print "Weird" or "Not Weird" based on parity/range rules.

N = int(input())

if N % 2 != 0:
    print("Weird")
elif 2 <= N <= 5:
    print("Not Weird")
elif 6 <= N <= 20:
    print("Weird")
else:
    print("Not Weird")
