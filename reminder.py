
_days_of_the_week = ['m', 'tu', 'w', 'th', 'f', 'sa', 'su']
def get_dow_number(day_string):
    day_string = day_string.lower().strip()
    for i, dow in enumerate(_days_of_the_week):
        if day_string.startswith(dow):
            return i
    return None

def read_csv_file(fname):
    import csv
    import sets
    reader = csv.reader(open(fname, 'r'))

    data = []
    for row in reader:
        if not row:
            continue
        if row[0] and row[0][0] in [';', '#']: # skip comments
            continue
        if len(row) < 4:
            print "Row must have 4 items", row
            continue

        message = row[3].strip().replace('\\n', '\n')
        if not message:
            continue

        def apply_converter(func, *args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (KeyboardInterrupt, MemoryError, SystemExit):
                raise
            except:
                return None

        days = sets.Set()
        hours = sets.Set()
        minutes = sets.Set()
        for (set, divisor, convert, input) in [
            (days, 7, get_dow_number, row[0]),
            (hours, 24, int, row[1]),
            (minutes, 60, int, row[2]),
        ]:
            input = input.strip()
            if not input or input == '*':
                set.add(None)
                continue
            for item in input.split(';'):
                item = item.strip()
                if '-' in item:
                    start, end = item.split('-', 1)
                    start = apply_converter(convert, start.strip())
                    end = apply_converter(convert, end.strip())
                    if start is None or end is None:
                        continue
                    if start <= end:
                        set.update(range(start, end + 1))
                    else:
                        set.update([
                            number % divisor
                            for number in range(end, start + divisor + 1)
                        ])
                else:
                    set.add(apply_converter(convert, item))

        if None in days:
            days = None
        if None in hours:
            hours = None
        if None in minutes:
            minutes = None
        data.append( (days, hours, minutes, message) )

    return data


def lookup_messages(datetime, message_table):
    day = datetime.weekday()
    hour = datetime.hour
    minute = datetime.minute
    found_messages = []
    for (day_set, hour_set, minute_set, message) in message_table:
        if (day_set is None or day in day_set) \
        and (hour_set is None or hour in hour_set) \
        and (minute_set is None or minute in minute_set):
            found_messages.append(message)
    return found_messages


def main(csv_fname, opt_date=None, opt_time=None):
    import datetime

    now = datetime.datetime.now()
    if opt_date is not None:
        # Assume yyyy-mm-dd
        year, month, day = map(int, opt_date.split('-'))
        now = now.replace(year=year, month=month, day=day)
    if opt_time is not None:
        # Assume HH:MM
        hour, minute = map(int, opt_time.split(':'))
        now = now.replace(hour=hour, minute=minute)

    message_table = read_csv_file(csv_fname)

    messages_to_show = {
        'now': lookup_messages(now, message_table),
        '5': lookup_messages(now + datetime.timedelta(minutes=5), message_table),
        '10': lookup_messages(now + datetime.timedelta(minutes=10), message_table),
    }

    for message_type in ['10', '5', 'now']:
        for m in messages_to_show.get(message_type, []):
            send(m, message_type)


_titles = {
    'now': 'Now',
    '5': 'In 5 minutes',
    '10': 'In 10 minutes',
}

_icons = {
    'now': 'icon-now.png',
    '5': 'icon-5.png',
    '10':'icon-10.png',
}

_timeouts = {
    'now': 10,
    '5': 12,
    '10': 12,
}

def send(message, message_type):
    try:
        import PySnarl
    except ImportError:
        return 1
    import pywintypes
    try:
        PySnarl.snGetSnarlWindow()
    except pywintypes.error:
        return 2

    import os
    PySnarl.snShowMessage(
        message,
        _titles.get(message_type),
        timeout=_timeouts.get(message_type, 10),
        iconPath=os.path.abspath(_icons.get(message_type, 10)),
    )

    return 0


_base_dir = None
if __name__ == '__main__':
    import getopt
    import os
    import sys

    opt_date = None
    opt_time = None

    _base_dir = os.path.split(sys.argv[0])[0]
    for key, value in _icons.items():
        _icons[key] = os.path.join(_base_dir, value)

    options, args = getopt.getopt(sys.argv[1:], 'd:t:', ['date=', 'time='])
    for option, value in options:
        if option in ['-d', '--date']:
            opt_date = value
        elif option in ['-t', '--time']:
            opt_time = value

    if len(args) < 1:
        csv_fname = os.path.join(_base_dir, 'reminder.csv')
        if not os.path.exists(csv_fname):
            # Allowed alternative in case editing the CSV is a pain:
            csv_fname = os.path.join(_base_dir, 'reminder.txt')
    else:
        csv_fname = args[0]

    main(csv_fname, opt_date=opt_date, opt_time=opt_time)

