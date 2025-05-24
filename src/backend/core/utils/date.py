from datetime import datetime

__all__ = ("date_time",)


# Здесь и так все понятно
def date_time(date=datetime.now()) -> str:
    return date.strftime("%Y-%m-%d %H:%M:%S")
