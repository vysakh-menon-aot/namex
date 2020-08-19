"""
Test helpers for Name Requests.
"""
import pytest
import json

from tests.python.end_points.common.http import build_test_query, build_request_uri
from tests.python.end_points.common.logging import log_request_path

from tests.python.unit.test_setup_utils import build_nr
from tests.python.end_points.common.http import get_test_headers
# Import token and claims if you need it
# from tests.python.end_points.common.configuration import claims, token_header

from ..configuration import API_BASE_URI
from tests.python.common.test_name_request_utils import \
    pick_name_from_list, assert_name_has_name, assert_name_has_id, assert_applicant_has_id, \
    assert_field_is_mapped

from namex.models import State, User

"""
Add states
DRAFT - Unexamined name, submitted by a client
INPROGRESS - An examiner is working on this request
CANCELLED - The request is cancelled and cannot be changed
HOLD - A name approval was halted for some reason
APPROVED - Approved request, this is a final state
REJECTED - Rejected request, this is a final state
CONDITIONAL - Approved, but with conditions to be met. This is a final state
HISTORICAL - HISTORICAL
COMPLETED - COMPLETED - LEGACY state for completed NRs from NRO
EXPIRED	EXPIRED - LEGACY state for expired NRs from NRO
NRO_UPDATING - Internal state used when updating records from NRO
COND-RESERVE Temporary reserved state with consent required
RESERVED - Temporary reserved state between name available and paid.  Once paid it is set to APPROVED or CONDITIONAL approval.
"""
state_data = [
    # ('DRAFT', 'Unexamined name, submitted by a client'),
    # ('INPROGRESS', 'An examiner is working on this request'),
    # ('CANCELLED', 'The request is cancelled and cannot be changed'),
    # ('HOLD', 'A name approval was halted for some reason'),
    # ('APPROVED', 'Approved request, this is a final state'),
    # ('REJECTED', 'Rejected request, this is a final state'),
    # ('CONDITIONAL', 'Approved, but with conditions to be met. This is a final state'),
    # ('HISTORICAL', 'HISTORICAL'),
    # ('COMPLETED', 'COMPLETED - LEGACY state for completed NRs from NRO'),
    # ('EXPIRED', 'EXPIRED - LEGACY state for expired NRs from NRO'),
    # ('NRO_UPDATING', 'NRO_UPDATING - internal state used when updating records from NRO'),
    # TODO: These states are missing in Test DB
    ('COND-RESERVE', 'Temporary reserved state with consent required'),
    ('RESERVED', 'Temporary reserved state between name available and paid.  Once paid it is set to APPROVED or CONDITIONAL approval.')
]


@pytest.mark.skip
def assert_names_are_mapped_correctly(req_names, res_names):
    print('\n-------- Test names --------\n')
    for req_name in req_names:
        res_name = pick_name_from_list(res_names, req_name.get('name'))

        print('\nCompare request name: \n' + repr(req_name) + '\n')
        print('With response name: \n' + repr(res_name) + '\n')

        assert_name_has_name(res_name)

        if res_name and req_name.get('id', None) is None:
            # It's a new name make sure it has an ID set
            assert_name_has_id(res_name)
        if res_name and req_name.get('id', None) is not None:
            # The name existed, make sure the ID has not changed
            assert_field_is_mapped(req_name, res_name, 'id')

        # Make sure the choice is mapped correctly
        assert_field_is_mapped(req_name, res_name, 'choice')
        assert_field_is_mapped(req_name, res_name, 'designation')
        print('\n......................................\n')

    print('\n-------- Test names complete --------\n')


@pytest.mark.skip
def assert_applicant_is_mapped_correctly(req_applicant, res_applicant):
    print('\n-------- Test applicant --------\n')
    print('\nCompare request applicant: \n' + repr(req_applicant) + '\n')
    print('With response applicant: \n' + repr(res_applicant) + '\n')

    if res_applicant and req_applicant.get('partyId', None) is None:
        # It's a new applicant make sure it has an ID set
        assert_applicant_has_id(res_applicant)
    if res_applicant and req_applicant.get('partyId', None) is not None:
        # The applicant existed, make sure the ID has not changed
        assert_field_is_mapped(req_applicant, res_applicant, 'partyId')

    print('\n-------- Test applicant complete --------\n')


@pytest.mark.skip
def add_states_to_db(states):
    for code, desc in states:
        state = State(cd=code, description=desc)
        state.save_to_db()


@pytest.mark.skip
def add_test_user_to_db():
    user = User(username='name_request_service_account', firstname='Test', lastname='User', sub='idir/name_request_service_account', iss='keycloak')
    user.save_to_db()


@pytest.mark.skip
def create_draft_nr(client, nr_data=None):
    """
    Create a draft NR, using the API, to use as the initial state for each test.
    :param client:
    :param nr_data:
    :return:
    """
    try:
        # Configure auth
        # token, headers = setup_test_token(jwt, claims, token_header)
        headers = get_test_headers()

        # Set up our test data
        add_states_to_db(state_data)
        add_test_user_to_db()

        # Optionally supply the field data
        nr = build_nr(State.DRAFT, nr_data)

        nr_data = nr.json()

        nr_data['applicants'] = [{
            'addrLine1': '1796 KINGS RD',
            'addrLine2': '',
            'addrLine3': '',
            'city': 'VICTORIA',
            'clientFirstName': '',
            'clientLastName': '',
            'contact': '',
            'countryTypeCd': 'CA',
            # 'declineNotificationInd': None,
            'emailAddress': 'bob.johnson@example.com',
            'faxNumber': '',
            'firstName': 'BOB',
            'lastName': 'JOHNSON',
            'middleName': '',
            # 'partyId': None,
            'phoneNumber': '2505320083',
            'postalCd': 'V8R 2P1',
            'stateProvinceCd': 'BC'

        }]

        nr_data['names'] = [{
            'name': 'BLUE HERON TOURS LTD.',
            'choice': 1,
            'designation': 'LTD.',
            'name_type_cd': 'CO',
            'consent_words': '',
            'conflict1': 'BLUE HERON TOURS LTD.',
            'conflict1_num': '0515211'
        }]

        # Create a new DRAFT NR using the NR we just created
        request_uri = API_BASE_URI
        test_params = [{}]

        query = build_test_query(test_params)
        path = build_request_uri(request_uri, query)
        log_request_path(path)

        post_response = client.post(path, data=json.dumps(nr_data), headers=headers)

        if not post_response or post_response.status_code != 201:
            raise Exception('NR POST operation failed, cannot continue with PATCH test')

        return post_response
    except Exception as err:
        print(repr(err))


@pytest.mark.skip
def patch_nr(client, action, nr_num, nr_data):
    try:
        request_uri = API_BASE_URI + nr_num + '/' + action
        test_params = [{}]

        headers = get_test_headers()
        query = build_test_query(test_params)
        path = build_request_uri(request_uri, query)
        print('Patch (' + action + ') Name Request [' + nr_num + ']: \n' + json.dumps(nr_data, sort_keys=True, indent=4, separators=(',', ': ')))
        log_request_path(path)

        patch_response = client.patch(path, data=json.dumps(nr_data), headers=headers)

        if not patch_response or patch_response.status_code != 200:
            # raise Exception('NR PATCH operation failed')
            pass

        return patch_response
    except Exception as err:
        print(repr(err))
        raise