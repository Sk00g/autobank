import re
from datetime import datetime

DATE_REGEX = '(JANu*a*r*y*|FEBr*u*a*r*y*|MARC*H*|APRi*l*|MAY|june*|july*|augu*s*t*|sept*e*m*b*e*r*|OCTo*b*e*r*|nove*m*b*e*r*|dece*m*b*e*r*|[0|1]*\d)[\.,/]*\s*([0-3]*\d)[\.,/]*\s*([1|2][9|0]\d\d|\d\d)'
MONTH_REGEX = '\d+\s*mo*n*t*h*s*'
NEWBORN_REGEX = 'newborn|new born'

def parse_stupid_dates(date_string):
    new_dates = []

    if not date_string:
        return None

    val = date_string.lower()
    matches = re.findall(DATE_REGEX, val, re.I)
    for match in matches:
        try:
            year = '19' + match[2] if len(match[2]) == 2 else match[2]
            if match[0].isalpha():
                month = match[0][:3]
                new_dates.append(datetime.strptime('-'.join([month, match[1], year]), "%b-%d-%Y"))
            else:
                new_dates.append(datetime.strptime('-'.join([match[0], match[1], year]), "%m-%d-%Y"))
        except:
            print('>>> ERROR: failed to parse date regex outcome %s from %s' % (str(match), val))

    return new_dates

def filter_months(age_string):
    regex = re.compile(MONTH_REGEX, re.I)
    new_string = regex.sub('1', age_string)
    regex = re.compile(NEWBORN_REGEX, re.I)
    return regex.sub('0', new_string)

# print(parse_stupid_dates('MAY 17, 1978  OCT 16, 1984'))
# print(parse_stupid_dates('MARCH 31, 1992, JUNE 18, 1990'))
# print(parse_stupid_dates('MARCH 6, 1971,JAN 2/61'))
# print(parse_stupid_dates('5/07/1976/NOV16/1973'))
#
# print()
#
# print(filter_months('6 MONTHS, 3'))
# print(filter_months('6MONTHS, 2'))
# print(filter_months('8,4,3,2,5MOS, 12,12'))
# print(filter_months('9, 8, 4, 18 MOS'))
# print(filter_months('9, NEW BORN'))
# print(filter_months('9, NEWBORN'))
# print(filter_months('9, new born'))