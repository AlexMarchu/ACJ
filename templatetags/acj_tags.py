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
def get_item(dictionary, key):
    return dictionary.get(key, '')
