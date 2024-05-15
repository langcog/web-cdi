def make_str_fun(s):
    if not type(s) in [str, float]:
        s = s.decode("utf-8")
        return s
    else:
        return s
