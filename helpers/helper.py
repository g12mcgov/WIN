


def cache(fn):
    """ Cache function calls to insert into Redis """

    holder = {}

    def wrapped(*args):
        # Key -> Val
        # arg1=1 arg2=2 -> 3
        if args in holder:
            return holder[args]
       
        result = fn(*args)
        holder[args] = result
        
        return result

    return wrapped