class CoolClass:
    def __init__(self, v):
        self.printStmnt = v

    def superPrint(self):
        print(self.printStmnt)


class CoolClassDerived(CoolClass):
    def __init__(self, v):
        super().__init__(v)

    def getObj(self):
        return CoolClassObj(super())


class CoolClassObj:
    def __init__(self, v):
        self.super = v

    def callPrint(self):
        self.super.superPrint()


myObj = CoolClassDerived("This worked!!!!")
myObj_discard = CoolClassDerived("This is another object!!!")

myObj2 = myObj.getObj()
myObj2.callPrint()


def f(x, y, z):
    x * y + z


def curried_f():
    def f(x):
        def g(y):
            def h(z):
                return x * y + z

            return h

        return g

    return f
