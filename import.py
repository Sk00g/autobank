import requests
import time
import json
import csv
import utils
from datetime import datetime, timedelta
from client_generator import add_household
# from client_generator_fast import add_household

"""TODO:
- Household logic
- The final touch will be the actual automation
"""


# first_name,first_name_1,first_name_2,last_name,city,birthdate,birthdate_1,birthdate_2,cohab,
# income,single_couple,children_number,children_ages,wild_meat,
# powdered_milk,dietary,comments,creation_date,phone,hamper_1,hamper_2,last_visit#

class Household:
    def __init__(self):
        self.primary = None
        self.secondary = None
        self.relationship = None
        # List of birthdate estimates
        self.children = []

    def size(self):
        return 2 + len(self.children) if self.secondary else 1 + len(self.children)

    def __str__(self):
        count = 1
        if self.secondary:
            count = 2
        count += len(self.children)
        members = self.primary.first_name + ' ' + self.primary.last_name
        if self.secondary:
            members += ', ' + self.secondary.first_name + ' ' + self.secondary.last_name
        for child in self.children:
            members += ', ' + child.first_name
        return "%d members: %s (%s)" % (count, members, self.primary.last_name)

class Client:
    def __init__(self):
        self.first_name = None
        self.last_name = None
        self.city = None
        self.birthdate = None
        self.creation_date = None
        self.cohab = None
        self.spouse = None
        self.income = None
        self.children = []
        self.gender = None
        self.dietary = ''
        self.dietary_items = []
        self.comments = ''
        self.first_visit = None
        self.last_visit = None
        self.phone = None
        self.notes = ''
        self.household = None

    def uid(self):
        return self.first_name + self.last_name + self.birthdate.year + self.birthdate.month + self.birthdate.day

    def __str__(self):
        return "%s %s (%s)" % (self.first_name, self.last_name, str(self.birthdate))


print('... beginning autobank automation script')

existing_clients = []

with open('link2feed_export2.csv') as file:
    reader = csv.DictReader(file, delimiter=',', quotechar='"')
    for row in reader:
        existing_clients.append({
            'last_name': row['Client Last Name'].title(),
            'first_name': row['Client First Name'].title(),
            'birthdate': datetime.strptime(row['Client Date of Birth'], "%Y-%m-%d")
        })
        cohab_last, cohab_first, cohab_bd = (row['HH Mem 1- Last Name'], row['HH Mem 1- First Name'], row['HH Mem 1- Date of Birth'])
        if cohab_last and cohab_first.find('KID') == -1 and cohab_bd:
            existing_clients.append({
                'last_name': cohab_last.title(),
                'first_name': cohab_first.title(),
                'birthdate': datetime.strptime(cohab_bd, "%Y-%m-%d")
            })

clients = []
households = []
incomplete = []
unmatched_cohab_names = []
duplicates = []
fails = 0

def client_exists(first_name, last_name, birthdate):
    for existing in existing_clients:
        if existing['first_name'] == first_name and existing['last_name'] == last_name and existing['birthdate'] == birthdate:
            return True
    return False

# Pre-load data parsing
def find_client(first_name, last_name, birthdate):
    for existing in clients:
        if first_name == existing.first_name and last_name == existing.last_name and birthdate == existing.birthdate:
            return existing
    return None

def add_gender(test_client):
    # test_client.gender = None
    # try:
    response = requests.get('http://api.genderize.io/?name=' + test_client.first_name)
    if response.status_code == 200:
        data = response.json()
        if data['gender']:
            if float(data['probability']) >= 0.8:
                test_client.gender = data['gender']
        else:
            print('>>> Gathering gender failed: could not match name')
    # except Exception as err:
    #     print('>>> Gathering gender failed: %s' % str(err))

def reject(data, reason, duplicate=False):
    global fails
    fails += 1
    print('>>> REJECT: %s' % reason)
    data['_reason'] = reason
    if duplicate:
        duplicates.append(json.dumps(data) + ',\n')
    else:
        incomplete.append(json.dumps(data) + ',\n')

def client_is_old(check):
    if not check.last_visit:
        return False

    visit_date = datetime.strptime(check.last_visit.replace('00:00:00', '').replace('MST', '').replace('MDT', ''),
                                                "%a %b %d %Y")
    return (datetime.now() - visit_date).days > 365 * 7

def update_client(updatee, data):
    data_creation = datetime.strptime(
        data['creation_date'].replace('00:00:00', '').replace('MST', '').replace('MDT', ''),
        "%a %b %d %Y")
    if data_creation > updatee.creation_date:
        print('\t>> Updated via newer %s' % first.creation_date)

    if data['city']:
        updatee.city = data['city']
    if data['dietary']:
        updatee.dietary += data['dietary'] + '\n'
    if data['wild_meat']:
        updatee.dietary += 'Wild Meat: %s\n' % data['wild_meat']
    if data['powdered_milk']:
        updatee.dietary += 'Powdered Milk: %s\n' % data['powdered_milk']
    if data['comments']:
        updatee.comments += data['comments']
    if data['phone']:
        updatee.phone = data['phone']
    if data['hamper_1']:
        updatee.notes += 'Hamper #1: %s\n' % data['hamper_1']
    if data['hamper_2']:
        updatee.notes += 'Hamper #2: %s\n' % data['hamper_2']
    if data['last_visit']:
        updatee.last_visit = data['last_visit']

with open('edited.csv', 'r') as file:
    reader = csv.DictReader(file, delimiter=',', quotechar='"')
    count = 0
    success = 0
    date_fails = 0
    age_fails = 0
    old_ignores = 0
    missing_infos = 0
    for row in reader:
        count += 1
        # print('>>> Parsing row %d' % count)
        # Check for reject data
        if not row['first_name_1'] or not row['last_name'] or not row['birthdate']:
            missing_infos += 1
            reject(row, 'incompleted basic information')
            continue

        new_clients = []

        # Clean extra spaces
        row['first_name_1'] = row['first_name_1'].strip()
        row['first_name_2'] = row['first_name_2'].strip()
        row['last_name'] = row['last_name'].strip()

        # Attempt to correct stupid dates
        date1, date2 = None, None
        try:
            date1 = datetime.strptime(row['birthdate_1'], "%Y-%m-%d")
        except:
            dates = utils.parse_stupid_dates(row['birthdate_1'])
            if len(dates) == 1:
                date1 = dates[0]
            elif len(dates) == 2:
                date1, date2 = dates
            else:
                reject(row, 'failed to parse date(s)')
                date_fails += 1
                continue

        # All birthdate_2 rows are proper format
        if row['birthdate_2']:
            date2 = datetime.strptime(row['birthdate_2'], "%Y-%m-%d")

        first = Client()
        second = None
        children = []

        first.first_name = row['first_name_1']
        first.last_name = row['last_name']
        # add_gender(first)
        first.birthdate = date1
        first.creation_date = datetime.strptime(row['creation_date'].replace('00:00:00', '').replace('MST', '').replace('MDT', ''),
                                                "%a %b %d %Y")
        first.last_visit = row['last_visit']
        if client_is_old(first):
            old_ignores += 1
            print('\t>> NOTE: ignoring old data %s' % first.last_visit)
            continue

        if client_exists(first.first_name, first.last_name, first.birthdate):
            reject(row, 'first client is already in system', True)
            continue

        match = find_client(first.first_name, first.last_name, first.birthdate)
        if match:
            reject(row, 'first client is duplicate', True)
            update_client(match, row)
            continue

        household = Household()
        household.primary = first
        first.household = household

        if row['first_name_2'] and date2:
            second = Client()
            second.first_name = row['first_name_2']
            second.last_name = row['last_name']
            # add_gender(second)
            second.birthdate = date2

            if client_exists(second.first_name, second.last_name, second.birthdate):
                reject(row, 'second client is already in system', True)
                continue

            match = find_client(second.first_name, second.last_name, date2)
            if match:
                # Do nothing if the household is already full
                if match.household.primary and match.household.secondary:
                    reject(row, 'matched spouse is in full house', True)
                    continue

                match.household.secondary = first
                first.household = match.household
                match.household.relationship = 'spouse'
                update_client(match, row)
                update_client(first, row)

                print("\t>> NOTE: adding %s to %s's household as spouse" % (str(first), str(match)))
                clients.append(first)

                continue
            else:
                household.secondary = second
                second.household = household
                household.relationship = 'spouse'
        elif row['cohab'] and date2:
            cohab = row['cohab']
            try:
                nfirst, nlast = cohab.split(' ')[0].strip(), cohab.split(' ')[1].strip()
                second = Client()
                second.first_name = nfirst
                second.last_name = nlast
                # add_gender(second)
                second.birthdate = date2

                if client_exists(second.first_name, second.last_name, second.birthdate):
                    reject(row, 'second client (cohab) is already in system', True)
                    continue

                match = find_client(nfirst, nlast, date2)
                if match:
                    # Do nothing if the household is already full
                    if match.household.primary and match.household.secondary:
                        reject(row, 'matched cohab is in full house', True)
                        continue

                    match.household.secondary = first
                    first.household = match.household
                    match.household.relationship = 'spouse'
                    update_client(match, row)
                    update_client(first, row)

                    print("\t>> NOTE: adding %s to %s's household as cohab" % (str(first), str(match)))
                    clients.append(first)

                    continue
                else:
                    household.secondary = second
                    second.household = household
                    household.relationship = 'commonlaw'
            except:
                print('\t>> ERROR: failed to parse cohab: %s' % cohab)

        first.income = row['income']
        if first.income == 'Works Part Time':
            first.income = "Works Part-Time"

        ages = []
        if row['children_ages']:
            try:
                ages = [int(txt.strip()) for txt in row['children_ages'].split(',')]
            except:
                save_attempt = utils.filter_months(row['children_ages'])
                print('\t>> ERROR: first level ages parse fail')
                try:
                    ages = [int(txt.strip()) for txt in save_attempt.split(',')]
                    print('\t>> SAVED: regex is awesome')
                except:
                    reject(row, 'failed to parse child ages')
                    age_fails += 1
                    continue
            child_count = 0
            for age in ages:
                child_count += 1
                new_child = Client()
                new_child.last_name = row['last_name']
                new_child.first_name = 'KID%d' % child_count
                new_child.birthdate = datetime(year = datetime.now().year - age, month=1, day=1)
                new_child.age = age
                new_child.city = row['city']
                household.children.append(new_child)

        if second:
            new_clients.append(second)
        new_clients.append(first)

        for client in new_clients:
            client.creation_date = datetime.strptime(
                row['creation_date'].replace('00:00:00', '').replace('MST', '').replace('MDT', ''),
                "%a %b %d %Y")
            client.last_visit = row['last_visit']
            if row['city']:
                client.city = row['city']
            if row['dietary']:
                client.dietary += row['dietary'] + '\n'
            if row['wild_meat']:
                client.dietary += 'Wild Meat: %s\n' % row['wild_meat']
            if row['powdered_milk']:
                client.dietary += 'Powdered Milk: %s\n' % row['powdered_milk']
            if row['comments']:
                client.comments += row['comments']
            if row['phone']:
                client.phone = row['phone']
            if row['hamper_1']:
                client.notes += 'Hamper #1: %s\n' % row['hamper_1']
            if row['hamper_2']:
                client.notes += 'Hamper #2: %s\n' % row['hamper_2']
            if row['last_visit']:
                client.notes += 'Last Visit: %s\n' % row['last_visit']


        clients_string = str(first)
        if second:
            clients_string += ', ' + str(second)
        if household.children:
            clients_string += '\n\t\t'
            for child in household.children:
                clients_string += 'CHILD: %d | ' % (datetime.now().year - child.birthdate.year)
        print('>>> Adding %d new clients: %s' % (len(new_clients), clients_string))
        clients.extend(new_clients)
        households.append(household)
        success += 1

        # if count > 1000:
        #     break

print('\n\n>>> Clients: %d' % len(clients))
print('>>> Households: %d' % len(households))
print('\t>>> Success: %d' % success)
print('\t>>> Failure: %d' % fails)
print('\t>>> Ignored: %d' % old_ignores)
print('\t\t>>> Date Parse Error: %d' % date_fails)
print('\t\t>>> Missing Basic Info Error: %d' % missing_infos)
print('\t\t>>> Child Age Parse Error: %d' % age_fails)
print('\t>>> PCT: %s' % round(success / (success + fails) * 100, 2))


# Send incompletes, duplicates, and unmatched cohabs to their own files
with open('incompletes.json', 'w+') as file:
    file.write('[\n')
    file.writelines(incomplete)
    file.write(']')
print('\n>>> Saved %d incompletes to file' % len(incomplete))
with open('duplicates.json', 'w+') as file:
    file.write('[\n')
    file.writelines(duplicates)
    file.write(']')
print('\n>>> Saved %d duplicates to file' % len(duplicates))
with open('unmatched.json', 'w+') as file:
    file.write('[\n')
    file.writelines(unmatched_cohab_names)
    file.write(']')
print('\n>>> Saved %d unmatched to file' % len(unmatched_cohab_names))

# DEBUG
# for house in households:
#     print(house.relationship)
# -----

print('count ' + str(len(households)))


for hh in households[2762:]:
    if hh.primary.birthdate.year > 2000 or hh.primary.birthdate.year < 1920:
        print('>>> (%d) Skipping due to age issue (%s)' % (households.index(hh), hh.primary))
        continue

    if hh.secondary and (hh.secondary.birthdate.year > 2000 or hh.secondary.birthdate.year < 1920):
        print('>>> (%d) Skipping due to age issue (%s)' % (households.index(hh), hh.secondary))
        continue

    print('>>> (%d) Gathering data for %s' % (households.index(hh), hh.primary))
    add_gender(hh.primary)
    print(hh.primary.gender)
    if hh.secondary:
        print('>>> Gathering gender for %s' % hh.secondary)
        add_gender(hh.secondary)
        print(hh.secondary.gender)
    add_household(hh)
    # print(hh.primary.gender)
    # print(hh.primary.income)
    # print(hh.size())
