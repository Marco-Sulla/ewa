"""
@author  Marco Sulla (marcosullaroma@gmail.com)
@date    2015-11-09
"""


import os
import calendar
import errno
from collections import Iterable
import shutil
from pathlib import Path
import json
import cmath

ispymssql = False

try:
    import pymssql
    ispymssql = True
except ImportError:
    pass
    

iso_fmt_file = "YYYY-MM-DDTHH-mm-ssZ"
number_re = r"([-+]?\d+(\.\d+)?([eE][-+]?\d+)?)|\bNaN\b|\bnan\b|\bNan\b"


class NaNError(ValueError):
    pass


class NoMatch(RuntimeError):
    pass


def mergeDicts(*dicts):
    len_dicts = len(dicts)
    
    if not len_dicts > 1: 
        err_tpl = "You must provide at least 2 arguments ({num} given)"
        raise TypeError(err_tpl.format(num=len_dicts))
        
    
    for i, d in enumerate(dicts):
        if i == 0: 
            z = d.copy()
        else:
            z.update(d)
    
    return z


def removeDupsFromDicts(dict_iterable):
    temp = [json.dumps(x, sort_keys=True) for x in dict_iterable]
    return (json.loads(x) for x in set(temp))


def dayStart(arr):
    return arr.replace(hour=0, minute=0, second=0, microsecond=0)


def monthStart(arr):
    arr2 = dayStart(arr)
    
    return arr2.replace(day=1)


def isoWeekNum(arr):
    return arr.datetime.isocalendar()[1]


def weekDay(d):
    return int(d.format("d"))


def isFestive(d):
    weekday = weekDay(d)
    
    return weekday in [6, 7]


def prevWorkingDay(d):
    while isFestive(d):
        d = d.replace(days=-1)
    
    prevday = d.replace(days=-1)
    
    while isFestive(prevday):
        prevday = prevday.replace(days=-1)
    
    return prevday


def getLastDayOfMonth(date):
    days_in_month = calendar.monthrange(date.year, date.month)[1]
    return dayStart(date.replace(day=days_in_month))


def mkdirP(path):
    try:
        os.makedirs(path, mode=0o700)
    except OSError as e:
        if not (e.errno == errno.EEXIST and os.path.isdir(path)):
            raise


def rmFile(path):
    try:
        try:
            os.remove(path)
        except TypeError:
            os.remove(str(path))
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


def overwrite(paths, dest_dir):
    def singleOverwrite(path):
        filename = os.path.basename(path)
        dest_path = os.path.join(dest_dir, filename)
        
        mkdirP(dest_dir)
        rmFile(dest_path)
        shutil.move(path, dest_dir)
    
    
    if isinstance(paths, Iterable):
        for path in paths:
            singleOverwrite(path)
    else:
        path = paths
        singleOverwrite(path)


def toAbsPath(path, abs_start):
    path = Path(path)
    abs_start = Path(abs_start)
    
    if path.is_absolute():
        res = path
    else:
        res = abs_start / path
    
    return res


def tarRelative(tar_f, path):
    tar_f.add(path, arcname=os.path.basename(path))


def minDeep(arg, exclude=None, no_nan=False):
    """
    Calculate min recursively for nested iterables, at any depth (arrays, 
    matrices, tensors...) and for any type of iterable (list of tuples, 
    tuple of sets, list of tuples of dictionaries...)
    """
    
    inf = float("+Inf")
    
    if exclude is None:
        exclude = ()
    
    if not isinstance(exclude, Iterable):
        exclude = (exclude, )
    
    if isinstance(arg, tuple(exclude)):
        return inf
    
    try:
        if next(iter(arg)) is arg:  # avoid infinite loops
            return min(arg)
    except TypeError:
        return arg
    
    try:
        mins = map(lambda x: minDeep(x, exclude), arg.keys())
    except AttributeError:
        try:
            mins = map(lambda x: minDeep(x, exclude), arg)
        except TypeError:
            return inf
    
    try:
        if no_nan:
            res = min((x for x in mins if not cmath.isnan(x)))
        else:
            res = min(mins)
    except ValueError:
        res = inf
    
    return res


def maxDeep(arg, exclude=None):
    """
    Calculate max recursively for nested iterables, at any depth (arrays, 
    matrices, tensors...) and for any type of iterable (list of tuples, 
    tuple of sets, list of tuples of dictionaries...)
    """
    
    minus_inf = float("-Inf")
    
    if exclude is None:
        exclude = ()
    
    if not isinstance(exclude, Iterable):
        exclude = (exclude, )
    
    if isinstance(arg, tuple(exclude)):
        return minus_inf
    
    try:
        if next(iter(arg)) is arg:  # avoid infinite loops
            return max(arg)
    except TypeError:
        return arg
    
    try:
        maxes = map(lambda x: maxDeep(x, exclude), arg.keys())
    except AttributeError:
        try:
            maxes = map(lambda x: maxDeep(x, exclude), arg)
        except TypeError:
            return minus_inf
    
    try:
        res = max(maxes)
    except ValueError:
        res = minus_inf
    
    return res


def magnitudeOrder(num):
    num_str = str(num)
    
    try:
        e_i = num_str.index("e")
    except ValueError:
        pass
    else:
        return int(num_str[e_i+1:])
    
    if len(num_str) == 1:
        return 0
    
    if num_str[0:1] == "0":
        order = -1
        
        for c in num_str[2:]:
            if c != "0":
                break
            
            order -= 1
    else:
        order = 0
        
        for c in num_str[1:]:
            if c == ".":
                break
            
            order += 1
    
    return order


def isInt(num):
    return num % 1 == 0


def dbString(dtype, user, password, host, port, db_name, service_name=False):
    if dtype == "oracle":
        type_verb = "oracle"
    elif dtype == "mysql":
        type_verb = "mysql+mysqlconnector"
    elif dtype == "postgres":
        type_verb = "postgresql"
    elif dtype == "mssql":
        if ispymssql:
            type_verb = "mssql+pymssql"
        else:
            type_verb = "mssql+pyodbc"
    else:
        raise RuntimeError("Unsupported db type: {t}".format(t=dtype))
    
    if dtype == "oracle" and service_name:
        db_tpl = ("{t}://{u}:{pw}@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)" + 
                  "(Host = {h})(Port={po}))" + 
                  "(CONNECT_DATA=(SERVICE_NAME = {d})))")
    else:
        db_tpl = "{t}://{u}:{pw}@{h}:{po}/{d}"
    
    if dtype == "mssql" and not ispymssql:
        db_tpl += "?driver=Microsoft+ODBC+Driver+for+SQL+Server"
    
    return db_tpl.format(
        t = type_verb,
        u = user,
        pw = password,
        h = host,
        po = port,
        d = db_name
    )
    

def tail(filepath):
    """
    @author Marco Sulla (marcosullaroma@gmail.com)
    @date May 31, 2016
    """
    
    try:
        filepath.is_file
        fp = str(filepath)
    except AttributeError:
        fp = filepath
    
    with open(fp, "rb") as f:
        size = os.stat(fp).st_size
        start_pos = 0 if size - 1 < 0 else size - 1
        
        if start_pos != 0:
            f.seek(start_pos)
            char = f.read(1)
            
            if char == b"\n":
                start_pos -= 1
                f.seek(start_pos)
            
            if start_pos == 0:
                f.seek(start_pos)
            else:
                char = ""
                
                for pos in range(start_pos, -1, -1):
                    f.seek(pos)
                    
                    char = f.read(1)
                    
                    if char == b"\n":
                        break
        
        return f.readline()
