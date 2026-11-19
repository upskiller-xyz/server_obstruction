"""Calendar helpers for a non-leap year"""

import numpy as np


class YearCalendar:
    """Converts days of a non-leap year to months and days of the month"""

    _MONTH_START_DAYS = np.array([1, 32, 60, 91, 121, 152, 182, 213, 244, 274, 305, 335])

    @classmethod
    def month_of(cls, day_of_year: np.ndarray) -> np.ndarray:
        """Month number (1-12) for each day of the year"""
        return np.searchsorted(cls._MONTH_START_DAYS, np.asarray(day_of_year), side="right")

    @classmethod
    def day_of_month(cls, day_of_year: int) -> int:
        """Day within the month for a day of the year"""
        month = int(cls.month_of(np.array([day_of_year]))[0])
        return int(day_of_year - cls._MONTH_START_DAYS[month - 1] + 1)
