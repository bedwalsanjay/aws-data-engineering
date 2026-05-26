def add_num_decor(func):
    def inner(*args, **kwargs):
        print("=========================")
        result = func(*args, **kwargs)
        print(result)   # print in middle
        print("=========================")
    return inner

@add_num_decor
def add_num(a, b):
    return a + b

add_num(2, 3)