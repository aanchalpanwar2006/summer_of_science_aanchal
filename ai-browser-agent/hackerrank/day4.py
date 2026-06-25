# Day 4: Class vs. Instance
# Person class with age; print "You are a/an X year old child/teenager/adult."

class Person:
    def __init__(self, initialAge):
        if initialAge < 0:
            print("Age is not valid, setting age to 0.")
            self.age = 0
        else:
            self.age = initialAge

    def amIOld(self):
        if self.age < 13:
            print(f"You are young.")
        elif self.age < 18:
            print(f"You are a teenager.")
        else:
            print(f"You are old.")

    def yearPasses(self):
        self.age += 1


t = int(input())
for _ in range(t):
    age = int(input())
    p = Person(age)
    p.amIOld()
    for _ in range(3):
        p.yearPasses()
    p.amIOld()
    print()
