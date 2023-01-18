from django import template

register = template.Library()


@register.filter()
def is_list(value):
    return isinstance(value, list)


@register.filter()
def get_dict_item(value, arg):
    value = value.get(arg)
    return value if value is not None else "none"


@register.filter()
def convert_none(value):
    return value if (value is not None and value != '') else "null"  # if value is None converts Python's None to JS's null


@register.filter()
def negate(boolean):
    return (not boolean).__str__()


@register.filter()
def get_ip_num(value):
    return value.split('_')[1]


@register.simple_tag
def url_help(url, item):
    params = url.split('&')
    r_params = params[:1]
    for param in params[1:]:
        if param == 'order_by=' + item + '-asc':
            r_params.append('order_by=' + item + '-desc')
        elif param == 'order_by=' + item + '-desc':
            r_params.append('order_by=' + item + '-asc')

    if len(r_params) == 1:
        r_params.append('order_by=' + item + '-asc')

    return '&'.join(x for x in r_params)
