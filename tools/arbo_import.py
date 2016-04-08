
from __future__ import unicode_literals
import six
import os, sys
import re
import openpyxl
from proteus import Model
from datetime import datetime
try:
    import cPickle as pickle
except ImportError:
    import pickle

datere =  re.compile('(\d{4})[-/](\d{2})[-/](\d{2})')


def get_model(model_name):
    return Model.get(model_name)
    # change this if we're integrated into tryton


def isyes(val):
    if val is None:
        return True, False
    elif isinstance(val, six.string_types):
        return True, val.strip().lower() in 'yes true on 1'
    else:
        return False, bool(val)


def isbool_true(val):
    return True, bool(val)


def isnotyes(val):
    k, v = isyes(val)
    return (k, not v)


def selection_lookup(val, field, model):
    '''
    looks at the .selection using the display-val as the key to lookup
    the stored value. It must match exactly (case insensitive)
    '''
    model_model = get_model(model)
    fieldmap = dict([(y, x) for x, y in model_model._fields[field]['selection']])
    if val in fieldmap:
        return True, fieldmap[val]
    else:
        return False, None


def lookup(val, model, field='name', extra_domain=None):
    model_obj = get_model(model)
    dom0 = [(field, '=', val)]
    dom1 = [(field, 'ilike', '%{}%'.format(str(val).lower()))]
    if extra_domain is None:
        extra_domain = []
    res = model_obj.find(dom0 + extra_domain)
    if res and len(res) == 1:
        return True, res[0]
    else:
        res = model_obj.find(dom1 + extra_domain)
        return False, res


def po_lookup(row, col, parish):
    try:
        lookup_val = resolve_val(row, col)
    except:
        pass
        lookup_val = False

    kgn_re = re.compile('Kgn +(\d+)', re.I)
    if lookup_val and kgn_re.match(lookup_val):
        lookup_val = lookup_val.replace('Kgn', 'Kingston')
    if lookup_val:
        return lookup(lookup_val, 'country.post_office',
                      extra_domain=[('subdivision', '=', parish.id)])
    return False, None


def make_altid(val, alt_id_type='other'):
    if val:
        return True, [('create', [{'alternative_id_type': 'other', 'code': val,
                      'comments': alt_id_type}])]
    else:
        return False, None


# COLMAP is a dict of dicts where the final values are the 1index from a row
# in the spreadsheet
COLMAP = {
    'party': {
        'lastname': 5, 'firstname': 4, 'dob': 7,
        'sex': (selection_lookup, 6, 'sex', 'party.party'),
        'unidentified': (isnotyes, 69)  # always returns True; BUG
    },
    'patient': {},
    'address': {
        'address_street_num': [8, 9], 'street': 10,
        'subdivision': (lookup, 13, 'country.subdivision', 'name',
                        [('country.code', '=', 'JM')]),
        'district_community': (lookup, 11, 'country.district_community'),
        'post_office': (po_lookup, 12),
        'desc': [12],

    },
    'contact': {
        'type': 'phone', 'value': 14,
    },
    'notification': {
        'diagnosis': (lookup, 'U06.9', 'gnuhealth.pathology', 'code'),
        'tracking_code': 2,
        'reporting_facility_other': 16, 'date_notified': 17, 'date_onset': 19,
        'hx_travel': (isyes, 21), 'hospitalized': (isyes, 61),
        'deceased': (isyes, 66),
        'specimen_taken': (isbool_true, 59),
        # 'specimens': [47, 48, 49, 50, 51, 52],
        'status': 63,
        'date_received': 18,
        'comments': ['Risk Factors:', 58, '\nOther Symptoms:', 55,
                     '\n Comments:\n', 67]
    },
    'specimen': {
        'date_taken': 59,
        'lab_test_type': 64,
        'specimen_type': 'unknown',
        'lab_result_state': (selection_lookup, 65, 'lab_result_state',
                             'gnuhealth.disease_notification.specimen'),
        'lab_result': [68]
    }
}

SYMPTOM_MAP = [
    (25, 'R19.7'),
    (26, 'R53.1'),
    (27, 'R29.5'),
    (28, 'R29.7'),
    (29, 'R60.2'),
    (30, 'R52.3'),
    (31, 'R52.4'),
    (32, 'R11.1'),
    (33, 'R50.9'),
    (35, 'R05'),
    (36, 'R06.0'),
    (37, 'R06.2'),
    (38, 'R07.4'),
    (39, 'R60.0'),
    (40, 'R56.0'),
    (41, 'R07.0'),
    (42, 'R21'),
    (43, 'R68.6'),
    (44, 'R68.7'),
    (45, 'R51'),
    (46, 'R53'),
    (47, 'R17'),
    (48, 'R29.1'),
    (49, 'R40'),
    (50, 'R40.1'),
    (51, 'R26'),
    (52, 'R04.2'),
    (53, 'R58'),
    (54, 'R04.0'),
    (56, 'R63.0'),
    (57, 'R51.1')
]
SYMPTOM_IDS = {}


def resolve_val(row, index_val):
    if isinstance(index_val, six.string_types):
        return index_val
    elif isinstance(index_val, (int, )):
        return row[index_val - 1].value
    elif isinstance(index_val, (list, )):
        return ' '.join(filter(None, [resolve_val(row, x) for x in index_val]))
    if isinstance(index_val, (tuple, )):
        fn = index_val[0]
        arg1 = resolve_val(row, index_val[1])
        args = [x for x in index_val[2:]]
        good, val = fn(arg1, *args)
        if good:
            return val
        else:
            raise Exception('Cannot resolve {}({}). Got \n{}'.format(
                            fn.func_name, repr(args), repr(val)))


# def resolve_as_date(s):
#     '''returns a datetime object made from s or None if it can't be converted'''
#     if s and datere.match(s):
#         date_parts = map(int, filter(None, datere.split(s.strip())))
#         try:
#             return datetime(*date_parts)
#         except Exception, e:
#             print('Cannot convert {} to date. Error was \n{}'.format(s, repr(e)))
#     return None


def make_object(row, map_key, initial_val=None):
    outdict = {}
    if initial_val:
        try:
            outdict.update(initial_val)
        except Exception, e:
            print('Cannot update dictionary with {}'.format(repr(e)))
    for key, index in COLMAP[map_key].items():
        try:
            val = resolve_val(row, index)
            outdict[key] = val
        except:
            pass
    return outdict


def make_address(row):
    # creates a dict for inclusion in the create for party
    parish_index = COLMAP['address']['subdivision']
    addr = make_object(row, 'address',
                       {'country': get_model('country.country')(89)})
    if addr and not addr.get('subdivision', False):
        try:
            subdiv = resolve_val(row, parish_index)
            addr['desc'] = ' '.join(filter(None, [addr.get('desc'),
                                                  'Parish', subdiv]))
        except:
            pass
    if addr and addr.get('subdivision') and not addr.get('post_office'):
        found, po = po_lookup(row, 12, addr.get('subdivision'))
        if found:
            addr['post_office'] = po
    return addr


def make_party_patient(row):
    # search for or create party, i.e. create the dict for party + patient
    party = make_object(row, 'party')
    try:
        party['name'] = "{lastname}, {firstname}".format(**party)
    except KeyError:
        party['name'] = ' '.join(filter(None, [party.get('firstname'),
                                 party.get('lastname')]))
    patient = {'name': party}

    if party.get('dob', False):
        lookupdom = [('dob', '=', party['dob'])]
    else:
        lookupdom = []
    found, fparty = lookup('{name}'.format(**party),
                           'party.party', extra_domain=lookupdom)
    if found:
        found, patient = lookup(fparty.id, 'gnuhealth.patient')
        if found:
            return True, patient
        else:
            return True, {'name': fparty}
    else:
        if fparty and len(fparty) > 1:
            print("multiple parties returned {}".format(
                  '\n'.join([x.name for x in fparty])))
            return False, fparty

    # let's setup the other stuff for the party
    # Alt ID
    alt_id = resolve_val(row, 69)
    if alt_id:
        _, party['alternative_ids'] = make_altid(alt_id, 'medical_record')

    # Occupation:
    oentry = resolve_val(row, 15)
    found, occupation = lookup(oentry, 'gnuhealth.occupation')
    if found:
        party['occupation'] = occupation
    elif oentry:
        patient['critical_info'] = 'Occupation: {}'.format(oentry)

    # Addresses
    addr = make_address(row)
    if len(addr) > 1:
        party['addresses'] = [('create', [addr])]

    # Contact mechanisms
    contact = make_object(row, 'contact')
    if len(contact) > 1 and contact.get('value'):
        party['contact_mechanisms'] = [('create', [contact])]

    return True, {'name': party}


def make_notification(row, patient):
    # create disease notification object
    notification = make_object(row, 'notification')
    if notification:
        notification['patient'] = patient
        if notification.get('specimen_taken', False):
            specimen = make_object(row, 'specimen')
            notification['specimens'] = [('create', [specimen])]
        symptoms = []
        for col in SYMPTOM_IDS:
            yes = resolve_val(row, (isyes, col))
            if yes:
                symptoms.append(
                    {'pathology': SYMPTOM_IDS[col]}
                )
                if col == 33:  # fever R50.9
                    fever_date_onset = resolve_val(row, 34)
                    if fever_date_onset:
                        symptoms[-1]['date_onset'] = fever_date_onset
        notification['symptoms'] = [('create', symptoms)]
        notification['patient'] = patient
    return notification


def process_xlfile(filepath):
    # open the file and get the current sheet
    workbook = openpyxl.load_workbook(filepath)
    pathology_model = get_model('gnuhealth.pathology')
    notification_model = get_model('gnuhealth.disease_notification')
    symptoms = pathology_model.find(
        [('code', 'in', [y for x, y in SYMPTOM_MAP])])
    symptom_code_id = dict([(x.code, x.id) for x in symptoms])
    SYMPTOM_IDS.update([(x, symptom_code_id[y]) for x, y in SYMPTOM_MAP])

    # on the first worksheet
    worksheet = workbook.worksheets[0]
    notifications = []
    bad_patient = []
    bad_notify = []
    good_notify = []
    tracking_field = COLMAP['notification']['tracking_code'] - 1
    # starting from the 2nd row:
    i = 0
    for row in worksheet.rows:
        # while worksheet.rows[i][1].value or worksheet.rows[i][5].value:
        # row = worksheet.rows[i]
        # check for notification using arbo number
        if i < 1:
            i += 1
            continue
        tracking_code = row[tracking_field].value
        found, notification = lookup(tracking_code,
                                     notification_model.__name__,
                                     'tracking_code')
        if found or len(notification) > 1:
            bad_notify.append(('existing', i+1))
            continue

        try:
            good, patient = make_party_patient(row)
        except Exception, e:
            good = False
            bad_patient.append(('error', i+1, e))

        if good:
            notification = make_notification(row, patient)
            try:
                print('creating notification {tracking_code}'.format(**notification))
                context = notification_model._config.context
                notifx = notification_model._proxy.create(notification, context)
                notifications.append(notifx)
                good_notify.append(i+1)
            except Exception, e:
                bad_notify.append(('error', i+1, e))
        i += 1

    results = {'badn': bad_notify, 'badppl': bad_patient,
               'goodn': good_notify, 'notifications': notifications}
    return results

if __name__ == '__main__':
    filename = sys.argv[1]
    if len(sys.argv) > 1:
        outfile = sys.argv[2]
    else:
        outfile = '{}.pypickle'.format(filename[:filename.rindex('.')])
    outdata = process_xlfile(filename)
    pickle.dump(outdata, open(outfile, 'wt'))
