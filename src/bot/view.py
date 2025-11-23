from datetime import date

from bot.keyboard import DAYS_OF_WEEK
from bot.models import FertilizingType, FrequencyType, Plant


def format_date(date: date | None) -> str:
    """Make date for user."""
    return date.strftime("%d.%m.%Y") if date else '—'


def localize_frequency_type(type: FrequencyType) -> str:
    """Return text for user."""
    return FrequencyType.get_text_map().get(type, str(type))


def localize_fertilizing_type(type: FertilizingType) -> str:
    """Return text for fertilizing."""
    return FertilizingType.get_text_map().get(type, str(type))


def format_period(period) -> str:
    """Форматирует период (WateringPeriod или FertilizingPeriod)."""
    if not period or not period.start or not period.end:
        return '—'
    return (
        f'{period.start.day:02d}.{period.start.month:02d} — '
        f'{period.end.day:02d}.{period.end.month:02d}'
    )


def format_schedule(schedule) -> str:
    """Make watering schedule info."""
    if not schedule:
        return '—'

    parts = [f'<b>Тип:</b> {localize_frequency_type(schedule.type)}']

    if isinstance(schedule.weekday, set) and schedule.weekday:
        weekdays = ', '.join(
            DAYS_OF_WEEK[day]
            for day in sorted(schedule.weekday)
            if 1 <= day <= 7
        )
        parts.append(f'<b>Дни недели:</b> {weekdays}')
    elif isinstance(schedule.weekday, int) and 0 <= schedule.weekday <= 6:
        parts.append(f'<b>День недели:</b> {DAYS_OF_WEEK[schedule.weekday]}')

    if schedule.monthday:
        parts.append(f'<b>День месяца:</b> {schedule.monthday}')

    if schedule.note:
        parts.append(f'<b>Примечание:</b> {schedule.note}')

    return '\n'.join(parts)


def format_fertilizing(fertilizing) -> str:
    """Make fertilizing info."""
    if not fertilizing:
        return '—'

    parts = []

    if fertilizing.frequency:
        type_map = {
            FertilizingType.days: (
                'день'
                if fertilizing.frequency == 1
                else 'дня' if fertilizing.frequency < 5 else 'дней'
            ),
            FertilizingType.weeks: (
                'неделю'
                if fertilizing.frequency == 1
                else 'недели' if fertilizing.frequency < 5 else 'недель'
            ),
            FertilizingType.months: (
                'месяц'
                if fertilizing.frequency == 1
                else 'месяца' if fertilizing.frequency < 5 else 'месяцев'
            ),
        }
        period_name = type_map.get(fertilizing.type, fertilizing.type.value)
        parts.append(
            f'<b>Частота:</b> раз в {fertilizing.frequency} {period_name}'
        )
    else:
        parts.append(
            f'<b>Тип:</b> {localize_fertilizing_type(fertilizing.type)}'
        )

    period = format_period(fertilizing)
    if period != '—':
        parts.append(f'<b>Период:</b> {period}')

    if fertilizing.note:
        parts.append(f'<b>Примечание:</b> {fertilizing.note}')

    return '\n'.join(parts)


def format_plant_message_html(plant: Plant) -> str:
    """Make HTML-message for Telegram."""
    warm_period = plant.warm_period
    cold_period = plant.cold_period
    fertilizing = plant.fertilizing

    warm_schedule = (
        format_schedule(warm_period.schedule) if warm_period else '—'
    )

    cold_schedule = (
        format_schedule(cold_period.schedule) if cold_period else '—'
    )

    parts = [
        f'🌿 <b>{plant.name}</b>',
        (f'<i>{plant.scientific_name}</i>' if plant.scientific_name else ''),
        '',
        (
            '📖 <b>Описание:</b>\n'
            f'{plant.description or 'Описание отсутствует.'}'
        ),
        '',
        '📅 <b>Период полива:</b>',
        (
            f'• <b>Тёплый период:</b> '
            f'{format_period(warm_period)}\n{warm_schedule}'
        ),
        '',
        (
            f'• <b>Холодный период:</b> '
            f'{format_period(cold_period)}\n{cold_schedule}'
        ),
        '',
        f'💧 <b>Последний полив:</b> ' f'{format_date(plant.last_watered_at)}',
        f'📆 <b>Следующий полив:</b> '
        f'{format_date(plant.next_watering_at)}',
        '',
        ('🌼 <b>Удобрение:</b>\n' f'{format_fertilizing(fertilizing)}'),
        '',
        (
            f'🪴 <b>Последнее удобрение:</b> '
            f'{format_date(plant.last_fertilized_at)}'
        ),
        (
            f'📆 <b>Следующее удобрение:</b> '
            f'{format_date(plant.next_fertilizing_at)}'
        ),
    ]

    return "\n".join(line for line in parts if line.strip())
