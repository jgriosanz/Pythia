import os
import sys
import inspect
import logging
import pathlib
from datetime import datetime, timedelta
from traitlets.config.loader import LazyConfigValue

from src.config import DFT_UTC_TS, LOG_LEVEL, LOG_FOLDER, VERBOSE


def get_logger(name="Pythia", to_stdout=False, level=LOG_LEVEL):
    """Creates a logger with the given name"""
    log_file = LOG_FOLDER.joinpath("name" + ".log")
    # TODO: Print to file as well and receive verbose level in the method
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if to_stdout:
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        logger.addHandler(ch)
    return logger


def bigint2utctimestamp(bigint):
    if bigint is None:
        return DFT_UTC_TS
    elif isinstance(bigint, str):
        bigint = int(bigint)
    return datetime.utcfromtimestamp(bigint / 1e3)


def in_ipynb(verbose=VERBOSE):
    """Detects if we are running within ipython (Notebook)"""
    try:
        cfg = get_ipython().config
        if isinstance(cfg['IPKernelApp']['parent_appname'], LazyConfigValue):
            if verbose > 2:
                print("Notebook detected")
            return True
        else:
            if verbose > 2:
                print("Running in script mode")
            return False
    except NameError:
        return False


class DelayedAssert:
    """
    Assert multiple conditions and report only after evaluating all of them

    Main 2 methods:
        expect(expr, msg=None)
        : Evaluate 'expr' as a boolean, and keeps track of failures

        assert_expectations()
        : raises an assert if an expect() calls failed

    Example:
        delayAssert = DelayedAssert()
        delayAssert.expect(3 == 1, 'Three differs from one')
        delayAssert.assert_expectations()
    """

    def __init__(self):
        self._failed_expectations = []

    def expect(self, expr, msg=None):
        """ keeps track of failed expectations """
        if not expr:
            self._log_failure(msg)

    def assert_expectations(self):
        """raise an assert if there are any failed expectations"""
        if self._failed_expectations:
            raise AssertionError(self._report_failures())

    def _log_failure(self, msg=None):
        (filename, line, funcname, contextlist) = inspect.stack()[2][1:5]
        filename = os.path.basename(filename)
        # context = contextlist[0].split('.')[0].strip()
        self._failed_expectations.append(
            'file "%s", line %s, in %s()%s'
            % (filename, line, funcname, (("\n\t%s" % msg) if msg else ""))
        )

    def _report_failures(self):
        if self._failed_expectations:
            (filename, line, funcname) = inspect.stack()[2][1:4]
            report = [
                "\n\nassert_expectations() called from",
                '"%s" line %s, in %s()\n'
                % (os.path.basename(filename), line, funcname),
                "Failed Expectations:%s\n" % len(self._failed_expectations),
            ]

            for i, failure in enumerate(self._failed_expectations, start=1):
                report.append("%d: %s" % (i, failure))
            self._failed_expectations = []
            return "\n".join(report)


def get_tabs(symbol, prev=7):
    n = len(symbol) + prev

    if in_ipynb():
        if n <= 15:
            return "\t" * 4
        elif n <= 21:
            return "\t" * 3
        elif n <= 27:
            return "\t" * 2
        elif n <= 33:
            return "\t"
        else:
            return ""
    else:
        if n <= 15:
            return "\t" * 4
        elif n <= 19:
            return "\t" * 3
        elif n <= 23:
            return "\t" * 2
        elif n <= 27:
            return "\t"
        else:
            return ""


def get_index(array, index, default=""):
    try:
        return array[index]
    except IndexError:
        return default


def datetime_format(date):
    if isinstance(date, datetime):
        return "%Y-%m-%d %H:%M:%S"
    else:
        return "%Y-%m-%d"


def ts2datetime(ts):
    return ts.strftime("%Y-%m-%dT%H:%M:%S")              #  '1999-12-13T00:00:00'


def datetime2ts(dt):
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S")


def first_day_of_month(day):
    return day.replace(day=1)


def last_day_of_month(day):
    next_month = day.replace(day=28) + timedelta(days=4)
    return next_month - timedelta(days=next_month.day)


def start_and_end_of_week(day):
    start_of_week = day - timedelta(days=day.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


def start_of_week(day):
    return start_and_end_of_week(day)[0]


def end_of_week(day):
    return start_and_end_of_week(day)[1]


def add_first_ts(info, first_date):
    """"""
    if not isinstance(info, dict):
        raise TypeError(f"info must be a dict, not {type(info)}")
    if not isinstance(first_date, datetime):
        LOG.error(f"first_date must be a datetime, not {type(first_date)}")
        return info

    if "FirstTimeStamp" in info.keys():
        prev_first_ts = info["FirstTimeStamp"]
        first_date = prev_first_ts if prev_first_ts <= first_date else first_date

    info["FirstTimeStamp"] = ts2datetime(first_date)
    return info


LOG = get_logger(name="Pythia", to_stdout=True, level=LOG_LEVEL)
