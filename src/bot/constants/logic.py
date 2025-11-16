from types import MappingProxyType

from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE

from bot.states import AddPlant


def make_immutable(obj):
    """Make dicts immutable."""
    if isinstance(obj, dict):
        return MappingProxyType(
            {key: make_immutable(value) for key, value in obj.items()}
        )
    return obj


DAYS_OF_WEEK = ('Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс')

FERTILIZING_INTERVAL_CONFIG = make_immutable(
    {
        'days': {
            'interval_text': 'дней',
            'state': AddPlant.fertilizing_every_n_days,
        },
        'weeks': {
            'interval_text': 'недель',
            'state': AddPlant.fertilizing_every_n_weeks,
        },
        'months': {
            'interval_text': 'месяцев',
            'state': AddPlant.fertilizing_every_n_months,
        },
    }
)

WATERING_FREQUENCY_CONFIG = make_immutable(
    {
        'weekly': {
            'text': (
                '📅 Выбери дни недели для {period} периода (можно несколько):'
            ),
            'kb': {'single_choice': False},
            'state_suffix': 'freq_days',
        },
        'biweekly': {
            'text': (
                '📆 Выбери день недели для {period} периода '
                '(один раз в две недели):'
            ),
            'kb': {'single_choice': True},
            'state_suffix': 'freq_day',
        },
        'monthly': {
            'text': (
                '🗓️ Введи день месяца для {period} периода (число от 1 до 31):'
            ),
            'kb': None,
            'state_suffix': 'freq_day_of_month',
        },
    }
)

TEXT_REQUIRED_FILTER = make_immutable(
    {
        AddPlant.name: (
            'Пожалуйста, отправь текстовое сообщение с названием растения.'
        ),
        AddPlant.description: (
            'Пожалуйста, отправь текстовое сообщение с описанием растения.'
        ),
        AddPlant.warm_start: (
            'Пожалуйста, отправь текстовое сообщение с датой начала '
            'теплого периода в формате ДД-ММ'
        ),
        AddPlant.warm_end: (
            'Пожалуйста, отправь текстовое сообщение с датой окончания '
            'тёплого периода в формате ДД-ММ.'
        ),
        AddPlant.fertilizing_start: (
            'Пожалуйста, отправь текстовое сообщение с датой начала '
            'подкормок в формате ДД-ММ.'
        ),
        AddPlant.fertilizing_end: (
            'Пожалуйста, отправь текстовое сообщение с датой окончания '
            'подкормок в формате ДД-ММ.'
        ),
    }
)


ALL_STATES = make_immutable(
    {
        'AddPlant': AddPlant,
    }
)
STATE_MESSAGES = make_immutable(
    {
        AddPlant.name: '✏️ Введи название растения.',
        AddPlant.description: '📝 Напиши короткое описание растения.',
        AddPlant.image: '📸 Отправь фото растения.',
        AddPlant.warm_start: '🌤 Введи дату начала тёплого периода (ДД-ММ).',
        AddPlant.warm_end: '❄️ Введи дату окончания тёплого периода (ДД-ММ).',
        AddPlant.warm_freq_type: '💧 Укажи частоту полива в тёплый период.',
        AddPlant.cold_freq_type: '💧 Укажи частоту полива в холодный период.',
        AddPlant.fertilizing_start: '🌱 Введи дату начала подкормок (ДД-ММ).',
        AddPlant.fertilizing_end: '🌾 Введи дату окончания подкормок (ДД-ММ).',
        AddPlant.fertilizing_frequency_type: '📅 Укажи тип частоты подкормок.',
        AddPlant.fertilizing_every_n_days: (
            'Введите интервал подкормок (в днях).'
        ),
        AddPlant.fertilizing_every_n_weeks: (
            'Введите интервал подкормок (в неделях).'
        ),
        AddPlant.fertilizing_every_n_months: (
            'Введите интервал подкормок (в месяцах).'
        ),
    }
)

WEEKDAY_MAP = make_immutable([MO, TU, WE, TH, FR, SA, SU])
