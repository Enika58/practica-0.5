"""Вспомогательные функции и утилиты."""


def format_phone(phone):
    """Форматирование номера телефона."""
    if not phone:
        return ''
    digits = ''.join(c for c in phone if c.isdigit())
    if len(digits) == 10:
        return f'+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}'
    elif len(digits) == 11:
        return f'+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}'
    return phone


def format_datetime(dt):
    """Форматирование даты и времени."""
    if not dt:
        return ''
    return dt.strftime('%d.%m.%Y %H:%M')


def format_date(dt):
    """Форматирование даты."""
    if not dt:
        return ''
    return dt.strftime('%d.%m.%Y')


def truncate_text(text, length=100):
    """Обрезка текста до указанной длины."""
    if not text:
        return ''
    if len(text) <= length:
        return text
    return text[:length] + '...'


def priority_sort_key(requests):
    """Ключ сортировки по приоритету."""
    priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
    return sorted(requests, key=lambda r: priority_order.get(r.priority, 4))
