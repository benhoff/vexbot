import psutil


def cpu_times(*args, **kwargs):
    return psutil.cpu_times()


def cpu_count(logical=True, *args, **kwargs):
    cores = psutil.cpu_count(logical) 
    if cores == 1:
        word = 'Core'
    else:
        word = 'Cores'
    return '{} CPU {}'.format(cores, word)


def virtual_memory_percent(*arg, **kwargs):
    percent = psutil.virtual_memory().percent
    return '{}%'.format(percent)


def virtual_memory_total(*args, **kwargs):
    mb_conversion = 1024 * 1024
    total = int(psutil.virtual_memory().total / mb_conversion)
    return '{} Mb'.format(total)


def swap(*args, **kwargs):
    swap = psutil.swap_memory()
    used = swap.used
    total = swap.total
    mb_conversion = 1024 * 1024
    used = int(used/mb_conversion)
    total = int(total/mb_conversion)
    return 'Used: {} | Total: {}'.format(used, total)
