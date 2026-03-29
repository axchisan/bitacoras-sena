from datetime import date, timedelta
from dataclasses import dataclass
from app.config import get_settings


@dataclass
class BitacoraPeriod:
    number: int
    start: date
    end: date

    @property
    def label(self) -> str:
        return f"Desde {self.start.strftime('%d/%m/%Y')} hasta {self.end.strftime('%d/%m/%Y')}"

    @property
    def delivery_date(self) -> date:
        # Deliver 5 days after the period ends
        return self.end + timedelta(days=5)


def get_all_periods() -> list[BitacoraPeriod]:
    settings = get_settings()
    periods = []
    current_start = settings.bitacoras_start_date

    for i in range(settings.bitacoras_total):
        period_end = current_start + timedelta(days=settings.bitacoras_period_days - 1)
        periods.append(BitacoraPeriod(number=i + 1, start=current_start, end=period_end))
        current_start = period_end + timedelta(days=1)

    return periods


def get_period_for_bitacora(number: int) -> BitacoraPeriod:
    periods = get_all_periods()
    if number < 1 or number > len(periods):
        raise ValueError(f"Bitácora number must be between 1 and {len(periods)}")
    return periods[number - 1]


def get_current_bitacora_number() -> int:
    today = date.today()
    periods = get_all_periods()
    for period in periods:
        if period.start <= today <= period.end:
            return period.number
    # If today is past all periods, return the last one
    if today > periods[-1].end:
        return periods[-1].number
    return 1


def get_pending_bitacoras() -> list[BitacoraPeriod]:
    today = date.today()
    return [p for p in get_all_periods() if p.end < today]
