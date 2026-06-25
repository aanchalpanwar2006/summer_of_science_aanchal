# Day 2: Operators
# Given meal cost, tip %, tax %; compute and print total rounded to nearest dollar.

meal_cost = float(input())
tip_percent = int(input())
tax_percent = int(input())

tip = meal_cost * tip_percent / 100
tax = meal_cost * tax_percent / 100
total = round(meal_cost + tip + tax)

print(f"The total meal cost is {total} dollars.")
