"""Creation-time names for new experiments."""
import re
from datetime import datetime
from zoneinfo import ZoneInfo


PATTERN = re.compile(r"^\d{4}_\d{1,2}_\d{1,2}-\d{2}_\d{2}__[a-z0-9][a-z0-9_-]*$")


def timestamp_prefix(now=None):
    now = now or datetime.now(ZoneInfo("Asia/Shanghai"))
    if now.tzinfo is not None:
        now = now.astimezone(ZoneInfo("Asia/Shanghai"))
    return f"{now.year}_{now.month}_{now.day}-{now:%H_%M}"


def new_experiment_name(purpose, now=None):
    purpose = re.sub(r"[^a-z0-9_-]+", "_", purpose.lower()).strip("_")
    if not purpose:
        raise ValueError("experiment purpose must contain [a-z0-9_-]")
    return f"{timestamp_prefix(now)}__{purpose}"


def validate_new_experiment_name(name):
    if not PATTERN.fullmatch(str(name)):
        raise ValueError("new experiment name must match YYYY_M_D-HH_MM__purpose")
    datetime.strptime(str(name).split('__',1)[0], '%Y_%m_%d-%H_%M')
    return str(name)
