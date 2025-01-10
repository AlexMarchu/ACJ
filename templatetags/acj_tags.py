from django import template
from datetime import datetime

register = template.Library()


@register.simple_tag
def hours_between(start_date, end_date):
    delta = end_date - start_date
    hours, r = divmod(delta.total_seconds(), 3600)
    minutes = r // 60

    return f'{int(hours):02}:{int(minutes):02}'


@register.filter
def abbreviated_name(name):
    try:
        last_name, first_name = name.split()
        return f'{first_name[0]}. {last_name}'
    except Exception:
        return name


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')


@register.filter
def get_result_class_color(result):
    if result == '.':
        return ''
    return 'status-ok' if result[0] == '+' else 'status-wa'


@register.filter
def format_date(date):
    return date.strftime('%d.%m.%Y %H:%M')
