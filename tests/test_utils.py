"""This file includes testing helper functions"""
import re
from proteus import Model

def create_user(name, login, password, groups, email='', active=True):
    '''
       This function is used to create an external user that is able
       to login into tryton with permissions within the specified
       group. Group must already exist within trytond pool.
    '''
    assert isinstance(active, bool), \
    'Incorrect input:\nActive requires a bool and not %s' % type(active)

    user = {'name':name, 'login':login, 'password':password, 'groups':groups}

    for (key, value) in user.items():
        if not isinstance(value, str) or not value:
            if not isinstance(value, str) and value:
                print 'Incorrect input: \n%s requires a string not %s or' \
                % (key, type(value))
            else:
                print 'Incorrect input: \n{} must not be empty'.format(key)
            return

    if email and not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$',
                              email):
        print "Invalid email address"
        return
    # get_groups = Model.get('res.group')
    # groups = get_groups.find([('name', '=', groups)])
    # assert len(groups) > 0, 'The group you gave does not exist'

    user['active'] = active
    model = Model.get('res.user')
    # assert len(model.find([('login', '=', login)])) < 1, \
    # "Login {} already exist\nChoose a different login".format(login)

    new_user = model()
    new_user.name = name
    new_user.login = login
    new_user.password = password
    new_user.email = email
    new_user.active = active
    # new_user.groups.append(groups[0])
    return new_user

def create_party(first_name, last_name, ex_user, sex, code=None):
    """Tester for creating party, and returns it as a object"""
    get_party = Model.get('party.party')
    party = get_party()

    if sex.lower() == 'female':
        party.sex = 'f'
    elif sex.lower() == 'male':
        party.sex = 'm'
    else:
        party.sex = 'u'

    party.is_person = True
    party.is_healthprof = True
    party.firstname = first_name
    party.lastname = last_name
    party.internal_user = ex_user
    if code:
        party.code = code
    name = "%s %s" % (first_name, last_name)
    party.name = name

    return party

def create_health_professional(party):
    '''Creates an health professional from party; party must
       already be registered as a party.party model.
    '''
    get_healthprof = Model.get('gnuhealth.healthprofessional')
    healthprof = get_healthprof()
    healthprof.name = party

    return healthprof
