def autoEval(x, t):
    if type(x) is t:
        return x
    if type(x) is str or type(x) is unicode and t is not str:
        return t(eval(x))
    return t(x)
