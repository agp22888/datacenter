from django import template

register = template.Library()


@register.filter()
def is_list(value):

    return isinstance(value, list)


@register.filter()
def get_dict_item(value, arg):
    value = value.get(arg)
    print("value", value)
    return value if value is not None else "none"


@register.filter()
def convert_none(value):
    return value if value is not None else "null"  # if value is None converts Python's None to JS's null


@register.filter()
def negate(boolean):
    return (not boolean).__str__()
