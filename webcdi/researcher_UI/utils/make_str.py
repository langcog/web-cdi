def make_str_fun(s):
    if type(s) != str:
        s = s.decode("utf-8")
        return s
    else:
        return s
