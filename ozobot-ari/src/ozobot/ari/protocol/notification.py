from __future__ import annotations

from .base import Model, Notification
from .types import Intersection, TNamedColor


class MotionNotificationBody(Model):
    max_speed: float
    overshot_distance: float
    overshot_time: float


class MotionNotification(Notification):
    result: MotionNotificationBody


class LineNavigationColorNotificationBody(Model):
    colors: list[TNamedColor]


class LineNavigationNotification(Notification):
    result: LineNavigationColorNotificationBody | Intersection


class TimeOfFlightNotificationBody(Model):
    distance: float
    deviation: float
    ambient_rate: float
    signal_rate: float
    active_count: int
    timestamp: int


class TimeOfFlightNotification(Notification):
    result: TimeOfFlightNotificationBody
