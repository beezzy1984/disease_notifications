
from __future__ import unicode_literals
import six
import sys
import re
import openpyxl
from proteus import Model, config as pconfig
from datetime import date, datetime, timedelta
import pytz
try:
    import cPickle as pickle
except ImportError:
    import pickle


def localtime(current):
    '''returns a datetime object with local timezone. naive datetime
    assumed to be in utc'''
    if not current or not isinstance(current, (date, datetime)):
        return None
    tz = pytz.timezone('America/Jamaica')
    if current.tzinfo is None:
        # assume it's local. convert it to timezone aware
        cdt = datetime(*current.timetuple()[:6], tzinfo=tz,
                       microsecond=current.microsecond)
    else:
        cdt = current
    return cdt.astimezone(pytz.UTC)


def getdt(val):
    localdt = localtime(val)
    if localdt:
        return True, localdt
    else:
        return False, localdt


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

def tostr(val):
    if val:
        return True, unicode(val)
    else:
        return True, ''


def totype(val, type_conv):
    if val:
        return True, type_conv(val)
    else:
        return False, None


def isnotyes(val):
    k, v = isyes(val)
    return (k, not v)


def selection_lookup(val, field, model):
    '''
    looks at the .selection using the display-val as the key to lookup
    the stored value. It must match exactly (case insensitive)
    '''
    model_model = get_model(model)
    fieldmap = dict([(y.lower(), x)
                     for x, y in model_model._fields[field]['selection']])
    if isinstance(val, six.string_types):
        vallow = val.strip().lower()
    else:
        vallow = val
    if vallow in fieldmap:
        return True, fieldmap[vallow]
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
        altid_model = get_model('gnuhealth.person_alternative_identification')
        return altid_model(alternative_id_type='other', code=val,
                           comments=alt_id_type)
    else:
        return None


# COLMAP is a dict of dicts where the final values are the 1index from a row
# in the spreadsheet
COLMAP = {
    'party': {
        '_model': 'party.party',
        'lastname': 4, 'firstname': 5, 'dob': (getdt, 8),
        'sex': (selection_lookup, 6, 'sex', 'party.party'),
        # 'unidentified': (isnotyes, 4),  # always returns True; BUG
        'occupation': (lookup, 14, 'gnuhealth.occupation')
    },
    'patient': {
        '_model': 'gnuhealth.patient'
    },
    'address': {
        '_model': 'party.address',
        'address_street_num': (tostr, 9), 'street': (tostr, 10),
        'subdivision': (lookup, 13, 'country.subdivision', 'name',
                        [('country.code', '=', 'JM')]),
        'district_community': (lookup, 11, 'country.district_community'),
        'post_office': (po_lookup, 12)

    },
    # 'contact': {
    #     '_model': 'party.contact_mechanism',
    #     'type': 'phone', 'value': (totype, 13, str),
    # },
    'notification': {
        '_model': 'gnuhealth.disease_notification',
        'diagnosis': (lookup, 55, 'gnuhealth.pathology', 'code'),
        'tracking_code': 2,
        'reporting_facility_other': 15, 'date_notified': (getdt, 16),
        'date_onset': (getdt, 17),
        'hx_travel': (isyes, 19), 'hospitalized': (isyes, 54),
        'deceased': (isyes, 59),
        'specimen_taken': (isbool_true, 52),
        # 'specimens': [47, 48, 49, 50, 51, 52],
        'status': (selection_lookup, 56, 'status',
                   'gnuhealth.disease_notification'),
        'comments': ['Risk Factors:', 51, '\nOther Symptoms:', 50,
                     '\n Comments:\n', 60]
    },
    'specimen': {
        '_model': 'gnuhealth.disease_notification.specimen',
        'date_taken': (getdt, 52),
        'lab_test_type': (selection_lookup, 57, 'lab_test_type',
                          'gnuhealth.disease_notification.specimen'),
        'specimen_type': (selection_lookup, 53),
        'lab_result_state': (selection_lookup, 58, 'lab_result_state',
                             'gnuhealth.disease_notification.specimen')
    }
}

SYMPTOM_MAP = [
    (20, 'R19.7'),
    (21, 'R53.1'),
    (22, 'R29.5'),
    (23, 'R29.7'),
    (24, 'R60.2'),
    (25, 'R52.3'),
    (26, 'R52.4'),
    (27, 'R11.1'),
    (28, 'R50.9'),
    (29, 'R05'),
    (30, 'R06.0'),
    (31, 'R06.2'),
    (32, 'R07.4'),
    (33, 'R60.0'),
    (34, 'R56.0'),
    (35, 'R07.0'),
    (36, 'R21'),
    (37, 'R68.6'),
    (38, 'R68.7'),
    (39, 'R51'),
    (40, 'R51.1'),
    (41, 'R53'),
    (42, 'R17'),
    (43, 'R29.1'),
    (44, 'R40'),
    (45, 'R40.1'),
    (46, 'R26'),
    (47, 'R04.2'),
    (48, 'R58'),
    (49, 'R04.0'),
]
SYMPTOM_IDS = {}


def resolve_val(row, index_val):
    if isinstance(index_val, six.string_types + (bool, )):
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


def make_object(row, map_key, initial_val=None, overrides=None):
    outdict = {}
    if initial_val:
        try:
            outdict.update(initial_val)
        except Exception, e:
            print('Cannot update dictionary with {}'.format(repr(e)))
    for key, index in COLMAP[map_key].items():
        if key.startswith('_'):
            continue
        try:
            val = resolve_val(row, index)
            outdict[key] = val
        except:
            pass
    if overrides:
        try:
            outdict.update(overrides)
        except Exception, e:
            print('Cannot update dictionary with {} {}'.format(repr(overrides),
                  repr(e)))
    # print('outdict = {}'.format(repr(outdict)))
    model = get_model(COLMAP[map_key]['_model'])
    return model(**outdict)


def make_address(row):
    # creates a dict for inclusion in the create for party

    addr = make_object(row, 'address', {'country': 89})
    if addr and not addr.subdivision:
        parish_index = [COLMAP['address'][x] for x in
                        ['district_community', 'post_office', 'subdivision']]
        try:
            subdiv = resolve_val(row, parish_index)
        except:
            subdiv = None
        addr.desc = ' '.join(filter(None, [addr.desc, subdiv]))
        addr.post_office = None
    if addr and addr.subdivision and not addr.post_office:
        found, po = po_lookup(row, 12, addr.subdivision)
        if found:
            addr.post_office = po
    if addr.district_community and (not addr.post_office or
            (addr.district_community.post_office != addr.post_office)):
        addr.district_community = None
        if addr.subdivision:
            po_index = [COLMAP['address'][x] for x in
                        ['district_community', 'post_office']]
            try:
                poval = resolve_val(row, po_index)
            except:
                poval = None
            addr.desc = ' '.join(filter(None, [addr.desc, poval]))
    return addr


def make_party_patient(row):
    # search for or create party, i.e. create the dict for party + patient
    party = make_object(row, 'party', {'is_person': True, 'is_patient': True,
                                       'unidentified': True})
    patient_model = get_model(COLMAP['patient']['_model'])

    if party.dob:
        lookupdom = [('dob', '=', party.dob)]
    else:
        lookupdom = []
    found, fparty = lookup(party.name,
                           'party.party', extra_domain=lookupdom)
    if found:
        found, patient = lookup(fparty.id, 'gnuhealth.patient')
        if found:
            return True, patient
        else:
            return True, patient_model(name=fparty)
    elif fparty and len(fparty) > 1:
        print("multiple parties returned {}".format(
              '\n'.join([x.name for x in fparty])))
        return False, fparty

    patient = patient_model(name=party)

    # let's setup the other stuff for the party
    if not party.sex:
        party.sex = 'u'

    # Alt ID
    # alt_id = resolve_val(row, 69)
    # if alt_id:
    #     party.alternative_ids.append(make_altid(alt_id, 'medical_record'))

    # Occupation:
    oentry = resolve_val(row, 14)
    if not party.occupation:
        patient.general_info = 'Occupation: {}'.format(oentry)

    # Addresses
    addr = make_address(row)
    if addr.subdivision:
        if len(party.addresses) > 0:
            party.addresses[0] = addr
        else:
            party.addresses.append(addr)

    # Contact mechanisms
    # contact = make_object(row, 'contact')
    # if contact and contact.value:
    #     party.contact_mechanisms.append(contact)
    return True, patient


def make_notification(row, patient):
    # create disease notification object
    # notification_model = get_model('gnuhealth.disease_notification')
    symptom_model = get_model('gnuhealth.disease_notification.symptom')
    notification = make_object(row, 'notification', {'patient': patient})
    SMD = dict(SYMPTOM_MAP)
    for col in SYMPTOM_IDS:
        yes = resolve_val(row, (isyes, col))
        if yes:
            s = symptom_model(pathology=SYMPTOM_IDS[col])
            notification.symptoms.append(s)
            if SMD.get(col, '') == 'R50.9' and (col+1) not in SMD:
                fever_date_onset = resolve_val(row, col+1)
                if fever_date_onset:
                    s.date_onset = fever_date_onset

    if notification.specimen_taken:
        try:
            specimen = make_object(row, 'specimen', {'lab_sent_to': 'Unknown'},
                                   overrides={'specimen_type': 'unknown'})
        except:
            specimen = None
        finally:
            if specimen and specimen.date_taken:
                notification.specimens.append(specimen)
            else:
                notification.specimen_taken = False

    if not notification.date_notified:
        if notification.date_received:
            notification.date_notified = notification.date_received
        else:
            notification.date_notified = notification.create_date
    return notification


def check_or_duplicate(existing, new_row):

    if not isinstance(existing, (list, )):
        existing = [existing]
    notification_model = Model.get('gnuhealth.disease_notification')
    _, new_patient = make_party_patient(new_row)
    new_diagnosis = resolve_val(new_row, COLMAP['notification']['diagnosis'])
    # new_code = resolve_val(new_row, COLMAP['notification']['tracking_code'])
    # new_date = resolve_val(new_row, COLMAP['notification']['date_notified'])
    tocopy = None
    for n0 in existing:
        if (new_patient == n0.patient and new_diagnosis != n0.diagnosis):
            # same patient, different suspected case
            tocopy = n0
        else:
            # genuine duplicate. not desired. nothing to copy
            tocopy = None
            break

    if tocopy:
        copied, = notification_model.duplicate([tocopy])
        copied.diagnosis = new_diagnosis
        copied.save()
        return True, copied
    else:
        return False, None


def setup_symptoms():
    pathology_model = get_model('gnuhealth.pathology')
    symptoms = pathology_model.find(
        [('code', 'in', [y for x, y in SYMPTOM_MAP])])
    symptom_code_id = dict([(x.code, x.id) for x in symptoms])
    SYMPTOM_IDS.update([(x, symptom_code_id[y]) for x, y in SYMPTOM_MAP])


def process_xlfile(filepath, limit=-1):
    # open the file and get the current sheet
    workbook = openpyxl.load_workbook(filepath)
    notification_model_name = 'gnuhealth.disease_notification'

    setup_symptoms()
    # on the first worksheet
    worksheet = workbook.worksheets[0]
    notifications = []
    bad_patient = []
    bad_notify = []
    good_notify = []
    skipped = []
    tracking_field = COLMAP['notification']['tracking_code'] - 1
    # starting from the 2nd row:
    cnt = 0
    for i, row in enumerate(worksheet.rows):
        # while worksheet.rows[i][1].value or worksheet.rows[i][5].value:
        # row = worksheet.rows[i]
        # check for notification using arbo number

        if i < 1:
            continue

        if limit > 0 and cnt >= limit:
            break

        print('processing row {}, {}'.format(i, repr(resolve_val(row, 2))))

        tracking_code = row[tracking_field].value
        found, notification = lookup(tracking_code,
                                     notification_model_name,
                                     'tracking_code')

        if found or (notification and len(notification) > 1):
            copied, result = check_or_duplicate(notification, row)
            if copied:
                cnt += 1
                good_notify.append(i)
                notifications.append(result)
            else:
                skipped.append(('existing', i))
            continue

        try:
            good, patient = make_party_patient(row)
        except Exception, e:
            good = False
            bad_patient.append(('error', i, e))

        if good:
            notification = make_notification(row, patient)
            try:
                patient.name.save()
                patient.save()
                notification.save()
                notifications.append(notification)
                good_notify.append(i)
            except Exception, e:
                bad_notify.append(('error', i, e, notification))

    results = {'badn': bad_notify, 'badppl': bad_patient, 'skipped': skipped,
               'goodn': good_notify, 'notifications': notifications}
    return results

if __name__ == '__main__':
    filename = sys.argv[1]
    tryton_conf = sys.argv[2]
    if tryton_conf.startswith('http'):
        pconfig.set_xmlrpc(tryton_conf)

    if len(sys.argv) > 1:
        outfile = sys.argv[2]
    else:
        outfile = '{}.pypickle'.format(filename[:filename.rindex('.')])
    outdata = process_xlfile(filename)
    pickle.dump(outdata, open(outfile, 'wt'))
