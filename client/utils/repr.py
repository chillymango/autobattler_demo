from types import BuiltinFunctionType, FunctionType
from types import MethodType


# for future reference
# i think this idea was probably terrible
# and will leave it in here as general shame
# what a stupid idea

def to_dict(obj, recursed_objects=None):
    """
    Convert an object into a dictionary representation
    """
    output = {}
    # UGH using list instead of set() sucks but not everything is hashable so *shrug*
    # disgusting
    recursed_objects = recursed_objects or []  # keep track of visited objects
    for attr_name in dir(obj):
        if not attr_name[0].isalnum() or not attr_name[-1].isalnum():
            # drop any that's not a standard variable name
            continue
        attr = getattr(obj, attr_name)
        # do not allow recursion
        if attr in recursed_objects:
            print('{} already seen'.format(attr_name))
            continue

        recursed_objects.append(attr)
        if isinstance(attr, MethodType) or isinstance(attr, FunctionType) or isinstance(attr, BuiltinFunctionType):
            continue

        # examine all members of storage and continue combining as required
        # TODO: support more data structures here
        if isinstance(attr, list):
            print('{} is a list'.format(attr_name))
            import IPython; IPython.embed()
            output[attr_name] = [to_dict(x, recursed_objects=recursed_objects) for x in attr]
        elif isinstance(attr, dict):
            output[attr_name] = {
                x: to_dict(y, recursed_objects=recursed_objects) for x, y in attr.items()
            }
        elif issubclass(type(attr), obj.__class__):
            # if it's a nested component, keep looking
            output[attr_name] = to_dict(obj)
        output[attr_name] = attr

    return output
