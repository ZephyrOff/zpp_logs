from jinja2 import Environment
from datetime import datetime
import time
from zpp_color import fg, bg, attr
import sys
import os
import re
import inspect
import psutil
import platform

def sizeconvert(size):
    size = int(size)
    if size < 1024:
      return str(round(size / 1024.0)) + " Octets"
    elif size < 1024**2:
      return str(round(size / 1024.0, 3)) + " Ko"
    elif size < 1024**3:
      return str(round(size / (1024.0**2), 2)) + " Mo"
    else:
      return str(round(size / (1024.0**3), 2)) + " Go"

def list_disk():
    array = []
    for element in psutil.disk_partitions(all=True):
        if "cdrom" in element.opts:
            if element.fstype!="":
                info = psutil.disk_usage(element.device)
                array.append({"device": element.device, "mountpoint": element.mountpoint, "fstype": element.fstype, "total_size": sizeconvert(info.total), "used_size": sizeconvert(info.used), "free_size": sizeconvert(info.free), "percent": info.percent})

        else:
            info = psutil.disk_usage(element.device)
            array.append({"device": element.device, "mountpoint": element.mountpoint, "fstype": element.fstype, "total_size": sizeconvert(info.total), "used_size": sizeconvert(info.used), "free_size": sizeconvert(info.free), "percent": info.percent})

    return array

def get_disk_info(mountpoint):
    for disk in list_disk():
        if mountpoint.startswith(disk['mountpoint']):
            return disk


# --- Jinja2 Custom Functions ---
def jinja_fg(color_name):
    return fg(color_name)

def jinja_bg(color_name):
    return bg(color_name)

def jinja_attr(code):
    return attr(code)

def jinja_date(format_str):
    return datetime.now().strftime(format_str)

def jinja_epoch():
    return time.time()

def jinja_exc_info():
    return sys.exc_info()

def jinja_filename():
    stack = inspect.stack()
    return stack[-1].filename

def jinja_filepath():
    return dirname(jinja_filename())

def jinja_lineno():
    stack = inspect.stack()
    return stack[-1].lineno

def jinja_functname():
    stack = inspect.stack()
    if stack[-1].filename==stack[-2].filename:
        return stack[-2].function
    else:
        return stack[-1].function

def jinja_path():
    return os.path.abspath(os.getcwd())

def jinja_process():
    return psutil.Process().name()

def jinja_processid():
    return str(psutil.Process().pid)

def jinja_username():
    return os.getlogin()

def jinja_uid():
    return str(os.getuid())

def jinja_os_name():
    return platform.system()

def jinja_os_version():
    return platform.version()

def jinja_os_release():
    return platform.release()

def jinja_platform():
    return platform.platform()

def jinja_os_archi():
    return platform.architecture()[0]

def jinja_mem_total():
    virtual = psutil.virtual_memory()
    return sizeconvert(virtual.total)

def jinja_mem_available():
    virtual = psutil.virtual_memory()
    return sizeconvert(virtual.available)

def jinja_mem_used():
    virtual = psutil.virtual_memory()
    return sizeconvert(virtual.used)

def jinja_mem_free():
    virtual = psutil.virtual_memory()
    return sizeconvert(virtual.free)

def jinja_mem_percent():
    virtual = psutil.virtual_memory()
    return str(virtual.percent)

def jinja_swap_total():
    swap =  psutil.swap_memory()
    return sizeconvert(swap.total)

def jinja_swap_used():
    swap =  psutil.swap_memory()
    return sizeconvert(swap.used)

def jinja_swap_free():
    swap =  psutil.swap_memory()
    return sizeconvert(swap.free)

def jinja_swap_percent():
    swap =  psutil.swap_memory()
    return str(swap.percent)

def jinja_cpu_count():
    return str(psutil.cpu_count(logical=False))

def jinja_cpu_logical_count():
    return str(psutil.cpu_count(logical=True))

def jinja_cpu_percent():
    return str(psutil.cpu_percent(interval=0.1))

def jinja_current_disk_device():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return disk_info.get('device', '')

def jinja_current_disk_mountpoint():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return disk_info.get('mountpoint', '')

def jinja_current_disk_fstype():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return disk_info.get('fstype', '')

def jinja_current_disk_total():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return str(disk_info.get('total_size', ''))

def jinja_current_disk_used():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return str(disk_info.get('used_size', ''))

def jinja_current_disk_free():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return str(disk_info.get('free_size', ''))

def jinja_current_disk_percent():
    stack = inspect.stack()
    disk_info = get_disk_info(abspath(stack[1].filename))
    return str(str(disk_info.get('percent', '')))

def jinja_match(regex_pattern, value):
    return re.match(regex_pattern, value)


# --- Shared Jinja2 Environment ---
_shared_jinja_env = Environment()
_shared_jinja_env.globals['date'] = jinja_date
_shared_jinja_env.globals['epoch'] = jinja_epoch
_shared_jinja_env.globals['fg'] = jinja_fg
_shared_jinja_env.globals['bg'] = jinja_bg
_shared_jinja_env.globals['attr'] = jinja_attr
_shared_jinja_env.globals['exc_info'] = jinja_exc_info
_shared_jinja_env.globals['filename'] = jinja_filename
_shared_jinja_env.globals['filepath'] = jinja_filepath
_shared_jinja_env.globals['lineno'] = jinja_lineno
_shared_jinja_env.globals['functname'] = jinja_functname
_shared_jinja_env.globals['path'] = jinja_path
_shared_jinja_env.globals['process'] = jinja_process
_shared_jinja_env.globals['processid'] = jinja_processid
_shared_jinja_env.globals['username'] = jinja_username
_shared_jinja_env.globals['useruidname'] = jinja_uid
_shared_jinja_env.globals['os_name'] = jinja_os_name
_shared_jinja_env.globals['os_version'] = jinja_os_version
_shared_jinja_env.globals['os_release'] = jinja_os_release
_shared_jinja_env.globals['os_archi'] = jinja_os_archi
_shared_jinja_env.globals['platform'] = jinja_platform
_shared_jinja_env.globals['mem_total'] = jinja_mem_total
_shared_jinja_env.globals['mem_available'] = jinja_mem_available
_shared_jinja_env.globals['mem_used'] = jinja_mem_used
_shared_jinja_env.globals['mem_free'] = jinja_mem_free
_shared_jinja_env.globals['mem_percent'] = jinja_mem_percent
_shared_jinja_env.globals['swap_total'] = jinja_swap_total
_shared_jinja_env.globals['swap_used'] = jinja_swap_used
_shared_jinja_env.globals['swap_free'] = jinja_swap_free
_shared_jinja_env.globals['swap_percent'] = jinja_swap_percent
_shared_jinja_env.globals['cpu_count'] = jinja_cpu_count
_shared_jinja_env.globals['cpu_logical_count'] = jinja_cpu_logical_count
_shared_jinja_env.globals['cpu_percent'] = jinja_cpu_percent
_shared_jinja_env.globals['current_disk_device'] = jinja_current_disk_device
_shared_jinja_env.globals['current_disk_mountpoint'] = jinja_current_disk_mountpoint
_shared_jinja_env.globals['current_disk_fstype'] = jinja_current_disk_fstype
_shared_jinja_env.globals['current_disk_total'] = jinja_current_disk_total
_shared_jinja_env.globals['current_disk_used'] = jinja_current_disk_used
_shared_jinja_env.globals['current_disk_free'] = jinja_current_disk_free
_shared_jinja_env.globals['current_disk_percent'] = jinja_current_disk_percent
_shared_jinja_env.globals['re_match'] = jinja_match