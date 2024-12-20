import bittensor as bt

def explore_module(module, prefix=''):
    for attr_name in dir(module):
        if not attr_name.startswith('__'):
            attr = getattr(module, attr_name)
            full_name = f"{prefix}{attr_name}"
            print(full_name)
            if isinstance(attr, type):
                print(f"  (Class)")
            elif callable(attr):
                print(f"  (Function/Method)")
            if hasattr(attr, '__module__') and attr.__module__.startswith('bittensor'):
                explore_module(attr, prefix=full_name + '.')

print("Bittensor components:")
explore_module(bt)
