from datetime import date, datetime, timezone
from enum import StrEnum, auto

from beanie import (
    Document,
    Insert,
    PydanticObjectId,
    Replace,
    SaveChanges,
    before_event,
)
from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, WEEKLY, rrule
from pydantic import BaseModel, Field

from bot.constants import (
    NO_DAYS_ERROR,
    NO_SCHEDULE_ERROR,
    UNDEFINED_SCHEDULE_TYPE_ERROR,
    UNDEFINED_TYPE_ERROR,
    WEEKDAY_MAP,
)


class MonthDay(BaseModel):
    """Class for date data."""

    day: int = Field(ge=1, le=31)
    month: int = Field(ge=1, le=12)

    def as_date(self, year: int) -> date:
        """As date method."""
        return date(year, self.month, self.day)


class FrequencyType(StrEnum):
    """Frequency type enum."""

    weekly = auto()
    biweekly = auto()
    monthly = auto()

    @classmethod
    def get_weekly_types(cls) -> set:
        """Get weekly base types."""
        return {cls.weekly, cls.biweekly}

    @classmethod
    def get_text_map(cls) -> dict['FrequencyType', str]:
        """Return values for buttons."""
        return {
            cls.weekly: 'Дни недели',
            cls.biweekly: 'Раз в две недели',
            cls.monthly: 'Раз в месяц',
        }

    @classmethod
    def get_texts_and_callbacks(cls) -> tuple[list[str], list[str]]:
        """Return texts and callbacks for keyboards."""
        mapping = cls.get_text_map()
        texts = list(mapping.values())
        callbacks = [item.value for item in mapping.keys()]
        return texts, callbacks

    @classmethod
    def get_names(cls) -> list[str]:
        """Get enum names."""
        return [member.name for member in cls]


class WateringSchedule(BaseModel):
    """Model for watering schedule."""

    type: FrequencyType = FrequencyType.weekly
    weekday: set[int] | int | None = None
    monthday: int | None = None
    note: str | None = None


class WateringPeriod(BaseModel):
    """Model for watering periods."""

    start: MonthDay | None = None
    end: MonthDay | None = None
    schedule: WateringSchedule | None = None
    note: str | None = None

    def as_period(self) -> tuple[date, date]:
        """Convert values to dates."""
        current_year = date.today().year
        if self.start is None or self.end is None:
            raise ValueError()
        start = self.start.as_date(current_year)
        end = self.end.as_date(current_year)
        if start < end:
            return start, end
        if start < date.today():
            end += relativedelta(years=1)
        else:
            start -= relativedelta(years=1)
        return start, end


class FertilizingType(StrEnum):
    """Fertilizing frequency types enum."""

    days = auto()
    weeks = auto()
    months = auto()

    @classmethod
    def get_text_map(cls) -> dict['FertilizingType', str]:
        """Return values for buttons."""
        return {
            cls.days: 'Один раз в n дней',
            cls.weeks: 'Один раз в n недель',
            cls.months: 'Один раз в n месяцев',
        }

    @classmethod
    def get_texts_and_callbacks(cls) -> tuple[list[str], list[str]]:
        """Return texts and callbacks for keyboards."""
        mapping = cls.get_text_map()
        texts = list(mapping.values())
        callbacks = [item.value for item in mapping.keys()]
        return texts, callbacks

    @classmethod
    def get_names(cls) -> list[str]:
        """Get enum names."""
        return [member.name for member in cls]


class FertilizingPeriod(BaseModel):
    """Fertilizing period model."""

    start: MonthDay | None = None
    end: MonthDay | None = None
    frequency: int | None = None
    type: FertilizingType = FertilizingType.days
    note: str | None = None

    def as_period(self) -> tuple[date, date]:
        """Convert values to dates."""
        current_year = date.today().year
        if not self.start or not self.end:
            raise ValueError('No start or end for period')
        start = self.start.as_date(current_year)
        end = self.end.as_date(current_year)
        if start < end:
            return start, end
        if start < date.today():
            end += relativedelta(years=1)
        else:
            start -= relativedelta(years=1)
        return start, end


class Plant(Document):
    """Plant model."""

    user_id: int
    name: str
    scientific_name: str | None = None
    description: str | None = None
    image: str | None = None
    storage_key: str | None = None

    warm_period: WateringPeriod | None = Field(default_factory=WateringPeriod)
    cold_period: WateringPeriod | None = Field(default_factory=WateringPeriod)
    fertilizing: FertilizingPeriod | None = Field(
        default_factory=FertilizingPeriod
    )

    last_watered_at: date | None = None
    last_fertilized_at: date | None = None

    next_watering_at: date | None = None
    next_fertilizing_at: date | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @before_event(Insert)
    def on_insert_set_timestamps(self):
        now = datetime.now(timezone.utc)
        self.created_at = now

    @before_event([Replace, SaveChanges])
    def on_update_set_timestamps(self):
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    async def find_to_water_today(cls) -> list["Plant"]:
        """Find plants to water today."""
        today = date.today()
        start = datetime.combine(today, datetime.min.time())
        end = datetime.combine(today, datetime.max.time())

        return await cls.find(
            (cls.next_watering_at >= start),  # type: ignore[operator]
            (cls.next_watering_at <= end),  # type: ignore[operator]
            ((cls.last_watered_at < start)),  # type: ignore[operator]
        ).to_list()

    @classmethod
    async def get_all_ids(cls, user_id: int) -> list[str]:
        """Receive all ObjectId for users."""
        plants = await cls.find(cls.user_id == user_id).sort('+_id').to_list()
        return [str(plant.id) for plant in plants]

    @classmethod
    async def get_documents_by_ids(
        cls, telegram_id: int, ids: list[str]
    ) -> list['Plant']:
        """Receive documents by ObjectId."""
        object_ids = [PydanticObjectId(id_) for id_ in ids]
        plants = await cls.find_many(
            {"user_id": telegram_id, "_id": {"$in": object_ids}}
        ).to_list()
        id_map = {str(plant.id): plant for plant in plants}
        return [id_map[i] for i in ids if i in id_map]

    def next_watering_date(self) -> date:
        """Calculate next watering date."""
        last_watered = date.today()
        last_watered_dt = datetime.combine(last_watered, datetime.min.time())

        warm_period = _require_watering_period(self.warm_period)
        cold_period = _require_watering_period(self.cold_period)
        warm_start, warm_end = warm_period.as_period()
        _, cold_end = cold_period.as_period()

        if warm_start <= last_watered <= warm_end:
            period = warm_period
            next_period = cold_period
            period_end = warm_end
        else:
            period = cold_period
            next_period = warm_period
            period_end = cold_end

        rule = self._build_rrule(
            _require_watering_schedule(period.schedule),
            last_watered_dt,
        )
        next_dt = rule.after(last_watered_dt)

        if next_dt.date() > period_end:
            next_rule = self._build_rrule(
                _require_watering_schedule(next_period.schedule),
                datetime.combine(period_end, datetime.min.time()),
            )
            next_dt = next_rule.after(
                datetime.combine(period_end, datetime.min.time())
            )

        self.next_watering_at = next_dt.date()
        return self.next_watering_at

    def next_fertilizing_date(self) -> date:
        """Calculate new fertilizing date."""
        fertilizing = _require_fertilizing_period(self.fertilizing)
        last_fertilized = date.today()
        fert_start, fert_end = fertilizing.as_period()

        frequency = fertilizing.frequency
        if frequency is None:
            raise ValueError(NO_SCHEDULE_ERROR)

        if fertilizing.type == FertilizingType.days:
            delta = relativedelta(days=frequency)
        elif fertilizing.type == FertilizingType.weeks:
            delta = relativedelta(weeks=frequency)
        elif fertilizing.type == FertilizingType.months:
            delta = relativedelta(months=frequency)
        else:
            raise ValueError(UNDEFINED_TYPE_ERROR)

        fertilizing_date = last_fertilized + delta

        if fertilizing_date > fert_end:
            next_fert_start = fert_start + relativedelta(years=1)
            self.next_fertilizing_at = next_fert_start
        else:
            self.next_fertilizing_at = fertilizing_date

        return self.next_fertilizing_at

    def sync_watering_and_fertilizing(self):
        """Check synchronization for watering and fertilizing."""
        if (
            self.fertilizing
            and self.next_watering_at >= self.next_fertilizing_at
        ):
            return True
        return False

    def _build_rrule(
        self, schedule: WateringSchedule, start_dt: datetime
    ) -> rrule:
        """Build schedule for watering."""
        freq = WEEKLY if schedule.type in {'weekly', 'biweekly'} else MONTHLY
        interval = 2 if schedule.type == 'biweekly' else 1

        if freq == WEEKLY:
            weekday_value = schedule.weekday
            if isinstance(weekday_value, int):
                weekdays = [WEEKDAY_MAP[weekday_value]]
            elif isinstance(weekday_value, (set, list)):
                weekdays = [WEEKDAY_MAP[day] for day in weekday_value]
            else:
                raise ValueError(NO_DAYS_ERROR)

            return rrule(
                freq=WEEKLY,
                interval=interval,
                byweekday=weekdays,
                dtstart=start_dt,
            )

        elif freq == MONTHLY:
            day = schedule.monthday or start_dt.day
            return rrule(
                freq=MONTHLY,
                bymonthday=day,
                dtstart=start_dt,
            )

        raise ValueError(
            UNDEFINED_SCHEDULE_TYPE_ERROR.format(type=schedule.type)
        )

    class Settings:
        name = 'plants'


def _require_watering_period(
    period: WateringPeriod | None,
) -> WateringPeriod:
    if period is None:
        raise ValueError(NO_SCHEDULE_ERROR)
    return period


def _require_watering_schedule(
    schedule: WateringSchedule | None,
) -> WateringSchedule:
    if schedule is None:
        raise ValueError(NO_SCHEDULE_ERROR)
    return schedule


def _require_fertilizing_period(
    period: FertilizingPeriod | None,
) -> FertilizingPeriod:
    if period is None:
        raise ValueError(NO_SCHEDULE_ERROR)
    return period
