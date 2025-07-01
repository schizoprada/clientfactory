# ~/clientfactory/src/clientfactory/core/utils/parameters/construct.py
"""
...
"""

def sigparams(filternone: bool = False, **kwargs) -> dict:
    if filternone:
        return {k:v for k,v in kwargs.items() if v is not None}
    return kwargs
