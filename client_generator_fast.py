import autoit
import json
import time
from datetime import datetime

DEFAULT_TIME = 0.5

DATE_FORMAT = "%Y-%m-%d"


def write_duplicate(first_name, last_name, dob):
    with open('l2f_duplicates.json', 'a+') as file:
        file.write(json.dumps({'first': first_name, 'last': last_name, 'dob': dob.strftime(DATE_FORMAT)}))


def add_member(member, relationship, count):
    y = 864 - 32 * count
    autoit.mouse_click("left", 3732, y)

    time.sleep(2.0)

    autoit.mouse_click("left", 2475, 239)
    time.sleep(DEFAULT_TIME)
    autoit.send(member.last_name.upper())
    autoit.send('{TAB}')
    autoit.send(member.first_name.upper())
    autoit.send('{TAB}')
    time.sleep(DEFAULT_TIME)
    autoit.send(member.birthdate.strftime(DATE_FORMAT))
    autoit.send("{TAB}")
    time.sleep(1.0)

    if hex(autoit.pixel_get_color(2877, 223)) == '0xf4b04f':
        if member.first_name.find('KID') != -1:
            print('duplicated detected for KID')
            autoit.mouse_click("left", 2872, 292)
            time.sleep(3.0)
            y = 438
            while hex(autoit.pixel_get_color(2902, y)) != '0xe66252':
                y += 1
            autoit.mouse_click('left', 2902, y)
            time.sleep(2.0)
            autoit.mouse_click("left", 3101, 326)
            time.sleep(2.0)
        else:
            write_duplicate(member.first_name, member.last_name, member.birthdate)
            print('duplicate detected in household member %s' % str(member))
            return False

    autoit.mouse_click("left", 2567, 312)
    autoit.send('{TAB}')
    if member.gender == "female":
        autoit.send('{DOWN}')
    elif member.gender == "male":
        autoit.send('{DOWN}{DOWN}')
    else:
        autoit.send('{DOWN}{DOWN}{DOWN}{DOWN}')
    time.sleep(DEFAULT_TIME)
    autoit.send('{ENTER}')

    autoit.send('{TAB}')
    autoit.send('{DOWN}')
    time.sleep(DEFAULT_TIME)
    if relationship == 'spouse':
        autoit.send('{DOWN}')
    elif relationship == 'child':
        autoit.send('{DOWN}{DOWN}')
    else:
        for i in range(9):
            autoit.send('{DOWN}')
    time.sleep(DEFAULT_TIME)
    autoit.send('{ENTER}')

    if relationship == 'child':
        autoit.mouse_click("left", 2450, 350)
        time.sleep(DEFAULT_TIME)

    autoit.mouse_click("left", 2669, 423)
    time.sleep(DEFAULT_TIME)
    click_point_from_city_member(member.city)
    time.sleep(DEFAULT_TIME)
    if member.birthdate.year >= 2002:
        autoit.mouse_click("left", 3231, 754)
    else:
        autoit.mouse_click("left", 2449, 720)
        time.sleep(DEFAULT_TIME)
        autoit.mouse_click("left", 3231, 867)
    time.sleep(1.0)

    return True


def click_point_from_city_member(city):
    if city in ['Cranbrook', 'Elko', 'Grasmere', 'Jaffray', 'Wycliffe', 'Yahk']:
        x = 2889
    else:
        x = 3109

    if city in ['Cranbrook', 'Kimberley']:
        y = 420
    elif city in ['Elko', 'Moyie']:
        y = 446
    elif city in ['Grasmere', 'Wardner']:
        y = 471
    elif city in ['Jaffray', 'Wasa']:
        y = 497
    elif city in ['Wycliffe']:
        y = 526
    elif city == 'Yahk':
        y = 551
    else:
        y = 575

    autoit.mouse_click("left", x, y)


def click_point_from_city(city):
    if city in ['Cranbrook', 'Elko', 'Grasmere', 'Jaffray']:
        x = 2206
    elif city in ['Kimberley', 'Moyie', 'Wardner', 'Wasa']:
        x = 2608
    elif city in ['Wycliffe', 'Yahk']:
        x = 3011
    else:
        x = 3414

    if city in ['Cranbrook', 'Kimberley', 'Wycliffe']:
        y = 819 - 48
    elif city in ['Elko', 'Moyie', 'Yahk']:
        y = 843 - 48
    elif city in ['Grasmere', 'Wardner', None]:
        y = 865 - 48
    else:
        y = 893 - 48

    autoit.mouse_click("left", x, y)


# Must start in Clients -> Client Search
def add_household(household):
    print('>>> Starting entry for %s' % str(household))

    autoit.win_activate("Link2Feed Portal - Google Chrome")
    time.sleep(DEFAULT_TIME)

    prime = household.primary
    second = household.secondary

    autoit.mouse_click("left", 2281, 328)
    time.sleep(1.0)
    autoit.send('{TAB}')
    autoit.send('{DOWN}{DOWN}{DOWN}{DOWN}')
    time.sleep(DEFAULT_TIME)
    autoit.send('{ENTER}')
    autoit.send('{TAB}')
    time.sleep(DEFAULT_TIME)
    if prime.last_visit:
        visit_date = datetime.strptime(prime.last_visit.replace('00:00:00', '').replace('MST', '').replace('MDT', ''),
                                       "%a %b %d %Y")
        autoit.send(visit_date.strftime(DATE_FORMAT))
    else:
        autoit.send(prime.creation_date.strftime(DATE_FORMAT))
    autoit.send('{TAB}{UP}{TAB}')

    autoit.send(prime.last_name.upper())
    autoit.send('{TAB}')
    autoit.send(prime.first_name.upper())
    autoit.send('{TAB}')

    time.sleep(DEFAULT_TIME)
    autoit.send(prime.birthdate.strftime(DATE_FORMAT))
    time.sleep(DEFAULT_TIME)
    autoit.send('{TAB}')

    time.sleep(1.0)
    if hex(autoit.pixel_get_color(2877, 223)) == '0xf4b04f':
        write_duplicate(prime.first_name, prime.last_name, prime.birthdate)
        print('duplicate detected: %s' % str(prime))
        autoit.mouse_click("left", 3816, 15)
        time.sleep(4.0)
        autoit.send('{ENTER}')
        time.sleep(4.0)
        autoit.send('#3')
        time.sleep(10.0)
        autoit.mouse_click("left", 2246, 54)
        autoit.send('https://portal.link2feed.ca/org/2191/intake/')
        time.sleep(DEFAULT_TIME)
        autoit.send('{ENTER}')
        time.sleep(6.0)
        return

    autoit.send('{TAB}')

    if prime.gender == "female":
        autoit.send('{DOWN}')
    elif prime.gender == "male":
        autoit.send('{DOWN}{DOWN}')
    else:
        autoit.send('{DOWN}{DOWN}{DOWN}{DOWN}')
    time.sleep(DEFAULT_TIME)
    autoit.send('{ENTER}')

    if not second:
        autoit.mouse_click("left", 2206, 807)
    elif household.relationship == 'commonlaw':
        autoit.mouse_click("left", 2474, 808)
    elif household.relationship == 'spouse':
        autoit.mouse_click("left", 2207, 831)
    else:
        autoit.mouse_click("left", 3011, 807)
    time.sleep(DEFAULT_TIME)

    autoit.mouse_move(3832, 317, 0)
    time.sleep(DEFAULT_TIME)
    autoit.mouse_down("left")
    autoit.mouse_move(3832, 716)
    autoit.mouse_up("left")

    autoit.mouse_click("left", 2206, 171)
    autoit.mouse_click("left", 2922, 224)
    autoit.mouse_click("left", 3011, 680)
    click_point_from_city(prime.city)

    if prime.income == "Student Scholarship":
        autoit.mouse_click("left", 2207, 915)
    else:
        autoit.mouse_click("left", 2205, 964)

    if prime.phone:
        fixed_phone = prime.phone.replace('(', '').replace(')', '').replace('-', '')
        if len(fixed_phone) == 10:
            autoit.mouse_click("left", 2245, 486)
            time.sleep(DEFAULT_TIME)
            autoit.send(fixed_phone)

    autoit.mouse_wheel("down", 20)
    time.sleep(DEFAULT_TIME)

    member_count = 0
    if household.secondary:
        member_count += 1
        success = add_member(household.secondary, household.relationship, 1)
        if not success:
            return

    # for child in household.children:
    #     member_count += 1
    #     success = add_member(child, 'child', member_count)
    #     if not success:
    #         return

    autoit.mouse_click("left", 3726, 966)
    time.sleep(3.0)
    autoit.mouse_click("left", 2248, 547)
    time.sleep(DEFAULT_TIME)
    autoit.send('+{TAB}')
    time.sleep(DEFAULT_TIME)
    down_count = 1
    if not prime.income:
        down_count = 5
    elif prime.income == 'Child Benefits':
        down_count = 2
    elif prime.income == 'Disability / PWD':
        down_count = 3
    elif prime.income == 'Employment Insurance':
        down_count = 4
    elif prime.income == 'OAP / CPP':
        down_count = 6
    elif prime.income == 'Social Assistance':
        down_count = 8
    elif prime.income == 'Student Scholarship':
        down_count = 10
    elif prime.income == 'Works Casual':
        down_count = 11
    elif prime.income == 'Works Full-Time':
        down_count = 12
    else:
        down_count = 13

    for i in range(down_count):
        autoit.send('{DOWN}')

    autoit.send('{ENTER}')

    time.sleep(DEFAULT_TIME)

    autoit.mouse_click("left", 2246, 535)

    if not household.secondary:
        autoit.mouse_click("left", 3737, 736)
    else:
        autoit.mouse_click("left", 3738, 871)

    time.sleep(1.5)
    autoit.mouse_click("left", 3747, 769)
    time.sleep(1.5)
    autoit.mouse_click("left", 2762, 193)
    time.sleep(1.5)
    autoit.mouse_click("left", 3765, 353)
    time.sleep(DEFAULT_TIME)

    if prime.dietary:
        prime.dietary = prime.dietary.replace('+', '').replace('^', '').replace('!', '').replace('#', '')
        autoit.send('--DIET--{ENTER}')
        autoit.send(prime.dietary.replace('\n', '{ENTER}'))
        autoit.send('--DIET--{ENTER}')
    if prime.notes:
        prime.notes = prime.notes.replace('+', '').replace('^', '').replace('!', '').replace('#', '')
        autoit.send(prime.notes.replace('\n', '{ENTER}'))
        if household.children:
            autoit.send('Children: %s {ENTER}' % [child.age for child in household.children])
    if prime.comments:
        prime.comments = prime.comments.replace('+', '').replace('^', '').replace('!', '').replace('#', '')
        autoit.send(prime.comments.replace('\n', '{ENTER}'))

    autoit.mouse_click("left", 3113, 487)
    time.sleep(1.5)

    # Check for green services in case something went wrong
    if hex(autoit.pixel_get_color(2611, 192)) != '0x43a543':
        print('>>> Entry failed: green services check: %s' % hex(autoit.pixel_get_color(2611, 192)))
        exit(1)

    autoit.mouse_click("left", 2462, 49)
    time.sleep(DEFAULT_TIME)
    autoit.send('https://portal.link2feed.ca/org/2191/intake/')
    autoit.send('{ENTER}')

    print(">>> Finished entry for %s" % str(household))


