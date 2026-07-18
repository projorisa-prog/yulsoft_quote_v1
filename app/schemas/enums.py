from enum import Enum

class DayOfWeek(str, Enum):
    MON = "MON"
    TUE = "TUE"
    WED = "WED"
    THU = "THU"
    FRI = "FRI"
    SAT = "SAT"
    SUN = "SUN"

class PresetFrequency(str, Enum):
    WEEKLY_1 = "WEEKLY_1"
    WEEKLY_2 = "WEEKLY_2"
    WEEKLY_3 = "WEEKLY_3"
    WEEKLY_5 = "WEEKLY_5"
    DAILY = "DAILY"

PRESET_MAP = {
    PresetFrequency.WEEKLY_1: [DayOfWeek.MON],
    PresetFrequency.WEEKLY_2: [DayOfWeek.MON, DayOfWeek.THU],
    PresetFrequency.WEEKLY_3: [DayOfWeek.MON, DayOfWeek.WED, DayOfWeek.FRI],
    PresetFrequency.WEEKLY_5: [DayOfWeek.MON, DayOfWeek.TUE, DayOfWeek.WED, DayOfWeek.THU, DayOfWeek.FRI],
    PresetFrequency.DAILY: list(DayOfWeek),
}

class DiscountType(str, Enum):
    NONE = "NONE"
    PERCENT = "PERCENT"
    AMOUNT = "AMOUNT"

class DesignKey(str, Enum):
    CLASSIC = "classic"
    MODERN = "modern"
    COLOR = "color"

class QuoteStatus(str, Enum):
    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"
    CONVERTED = "CONVERTED"
    EXPIRED = "EXPIRED"

class UserPlan(str, Enum):
    FREE = "FREE"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"