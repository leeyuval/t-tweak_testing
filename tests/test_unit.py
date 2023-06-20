""" Example functions for Unit Test Class"""

import os
import sys
import json
import random
import datetime

import fastapi.exceptions
import pytest
from fastapi.testclient import TestClient
from fastapi import status as http_status

# Makes it easier to run in students' Windows's laptops, with no need to set path vars
sys.path.append(os.path.dirname(os.path.abspath(__name__)))
import main
import extra

# ***** Response Codes *****
OK_RESPONSE = 200

# ***** States *****
STANDBY_STATE = "StandBy"
INPUT_STATE = "Input"
ERROR_STATE = "Error"
QUERY_STATE = "Query"

# ***** Commands *****
CLEAR_COMMAND = "clear"
STOP_COMMAND = "stop"
SORRY_COMMAND = "sorry"
GET_STATE_COMMAND = "state"


# Client that gives us access to a dummy server for HTTP tests
client = None


# ---------------------------------------------------------------------------
# Setup and Teardown functions.
# These are examples of the functions used by pytest to prepare and dismantle
#   the entire test suite, or to prepare and dismantle each one of the tests.
#   You can, for example, setup services, states, or other operating environments.
# Advanced usage: You can also have setup/teardown functions for specific tests,
#   or for specific groups of tests.
#
# To see the output of the setup/teardown functions, run pytest with the argument:
#   --capture=no (as in pytest -v --capture=no)
# ---------------------------------------------------------------------------
def setup_module(module):
    print("\n==> THIS WILL HAPPEN *before all* THE TESTS BEGIN")
    # For example, copy test data into the test suite
    # For example, set a dummy server running (like the TestClient)
    print("==> START!")

    global client
    client = TestClient(main.app)


def teardown_module(module):
    print("\n==> THIS WILL HAPPEN *after all* THE TESTS END")
    # For example, delete test files and output files
    print("==> FINISH!")

    global client
    client = None


def setup_function():
    print("\n--> This will happen BEFORE each one of the tests begin")
    # For example, cleanup temp files
    # For example, get information on resources available


def teardown_function():
    print("\n--> This will happen AFTER each one of the tests ends")
    # For example, release handles


# ---------------------------------------------------------------------------
# TEST 1: Transform a text to lowercase. Simple!
# Amounts to 1 test in the total unit tests
# ---------------------------------------------------------------------------
def test_lower_ABCD():
    r = main.lower("ABCD")
    j = json.loads(r.body)
    assert r.status_code == OK_RESPONSE
    assert j["res"] == "abcd"


# ---------------------------------------------------------------------------
# TEST 2: Tests can be longer and/or consist of many checks.
#   Note this is a metamorphic test, we don't care about the actual strength
#       of the password or of the results of the first test. We just want the
#       tests to be consistent.
# Amounts to 1 test in the total unit tests
# ---------------------------------------------------------------------------
def test_password_length_score():
    password = "".join(random.choices("abcXYZ123!@#", k=20))

    while len(password) >= 1:
        r_large = main.password_strength(password)
        j_large = json.loads(r_large.body)

        password = password[:-1]
        r_small = main.password_strength(password)
        j_small = json.loads(r_small.body)

        assert OK_RESPONSE == r_large.status_code
        assert OK_RESPONSE == r_small.status_code
        assert j_large["res"] >= j_small["res"]


# ---------------------------------------------------------------------------
# TEST 3: Transform to uppercase a number of strings. Still simple, notice how
#   the framework allows to perform one test on multiple variables without
#   repeating the test.
# Amounts to 7 tests in the total unit tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "test,expected",
    [
        ("", ""),
        ("a", "A"),
        ("q3q5q7q10", "Q3Q5Q7Q10"),
        ("2q4q6q8q11q14q17q20q", "2Q4Q6Q8Q11Q14Q17Q20Q"),
        ("q3q5q7q10q13q16q19q22q25q", "Q3Q5Q7Q10Q13Q16Q19Q22Q25Q"),
        ("3", "3"),
        ("abc#$%def", "ABC#$%DEF"),
    ],
    ids=[
        "empty",
        "single letter",
        "10 chars",
        "20 chars",
        "long string",
        "digit",
        "special chars",
    ],
)
def test_upper_many(test, expected):
    r = main.upper(test)
    j = json.loads(r.body)
    assert r.status_code == OK_RESPONSE
    assert j["res"] == expected


# ---------------------------------------------------------------------------
# TEST 4: T-Tweak has our tweak functions (units) running on top of a web server
#   that has specific configurations to deal with the user input (so it's another unit).
#   Luckily fastapi let's us separate that unit as well with a dummy server.
# Amounts to 1 test in the total unit tests
# ---------------------------------------------------------------------------
def test_upper_rest_within_bv():
    r = client.get("upper/word")
    assert OK_RESPONSE == r.status_code
    assert "WORD" == r.json()["res"]


# ---------------------------------------------------------------------------
# TEST 5: Using the dummy server, for negative tests.
# Amounts to 1 test in the total unit tests
# 404: Page not found
# 422: Unprocessable Entity
# ---------------------------------------------------------------------------
def test_upper_rest_outside_bv():
    r = client.get("upper")
    assert 404 == r.status_code
    r = client.get("upper/-3-5-7-9-12-15-18-21-")
    assert 422 == r.status_code


# ---------------------------------------------------------------------------
# TEST 6: Functions with complex dependencies may require us to work around the
#   complexity by controlling some of the environment.
#   This is not always possible and not always effective.
# Amounts to 1 tests in the total unit tests
# ---------------------------------------------------------------------------
def test_random_naive():
    extra.reset_random(0)
    r = main.rand_str(4)
    j = json.loads(r.body)

    assert r.status_code == OK_RESPONSE
    assert j["res"] == "2yW4"

    r = main.rand_str(15)
    j = json.loads(r.body)

    assert r.status_code == OK_RESPONSE
    assert j["res"] == "Acq9GFz6Y1t9EwL"


# ---------------------------------------------------------------------------
# TEST 7: For functions with complex dependencies.
#   We can create a stub of the dependencies, replacing it with a fake function
#       of our own. Then we have full control.
# Amounts to 1 tests in the total unit tests
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "length",
    [1, 10, 20, 50],
)
def test_random_unit(monkeypatch, length):
    monkeypatch.setattr(main.extra, "get_rand_char", lambda: "t")
    r = main.rand_str(length)
    j = json.loads(r.body)
    assert r.status_code == OK_RESPONSE
    assert j["res"] == "t" * length


# ---------------------------------------------------------------------------
# TEST 8: T-Tweak functions also throw exceptions when something is not right
#   (for example, when we need to send a different HTTP status). We have to
#   test that too! Unit Test frameworks allow the test to expect a specific
#   Exception. Useful, uh?
# 409: Conflict
# Amounts to 1 test in the total unit tests
# ---------------------------------------------------------------------------
def test_with_exception():
    # 'raises' checks that the exception is raised
    with pytest.raises(fastapi.exceptions.HTTPException) as exc:
        main.substring("course 67778", 3, 2)
    assert http_status.HTTP_409_CONFLICT == exc.value.status_code


# ---------------------------------------------------------------------------
# TEST 9: Unit test frameworks allow setting conditions to skip tests.
#   Sometimes a test may be suitable for a platform but not another, for a version
#   but not another, etc.
# Amounts to 1 test in the total unit tests
# ---------------------------------------------------------------------------
@pytest.mark.skipif(fastapi.__version__ > "0.95", reason="requires fastapi <= 0.95")
def test_root_status():
    r = client.get("/")
    assert "Operational" == r.json()["res"]


# ---------------------------------------------------------------------------
# TEST 10: test_password_ec
# Automate the tests for equivalence classes of password function. The list of equivalence
#   partitions and sample values is given in the exercise document.
# The tests will reach 100% statement coverage of the password_strength function (line 323-369).
#   Hint: You will need to use:
#   - direct calls to main.password_stregth in order to receive scores for all examples
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "test,expected",
    [
        ("", 0),
        ("1", 0),
        ("Too-L0ng-4-the-allowed-input-length", 10),
        ("root", 0),
        ("password", 0),
        ("admin", 0),
        ("G00dShort", 7),
        ("gggggggg", 0),
        ("gfs98ased", 5),
        ("NOT1LOWCASE", 7),
        ("noDIGIT", 3),
        ("lowcaseonly", 5),
        ("UPCASEONLY", 4),
        ("1234567", 1),
        ("%@#$^&*", 0),
        ("L0ng-And-G00d", 10),
        ("aaaaaaaaaaaaaaaaaa", 0),
        ("l0ngbutnouppercase", 8),
        ("LONG1BUTNOLOWCASE", 8),
        ("LongButNotOneDigit", 8),
        ("longbutonlylowecase", 6),
        ("LONGBUTONLYUPCASE", 6),
        ("12345678901234", 6),
        ("%@#$%$%$%$%$%$%$", 4)
    ],
    ids=[
        "Length = 0",
        "0 < length <= 2",
        "Length > 20",
        "Password is 'root'",
        "Password is 'password'",
        "Password is 'admin'",
        "2 < length < 12, lowercase, upcase, digit",
        "2 < length < 12, all same char",
        "4 < length < 12, no uppercase",
        "4 < length < 12, no lowercase",
        "4 < length < 12, no digit",
        "4 < length < 12, lowcase only",
        "4 < length < 12, upcase only",
        "4 < length < 12, digit only",
        "6 < length < 12, special chars only",
        "12 < length, lowcase, upcase, digit",
        "12 < length, all same char",
        "12 < length, no uppercase",
        "12 < length, no lowercase",
        "12 < length, no digit",
        "12 < length, lowcase only",
        "12 < length, upcase only",
        "12 < length, digit only",
        "12 < length, special chars only"
    ],
)
def test_password_ec(test, expected):
    r = main.password_strength(test)
    j = json.loads(r.body)
    assert r.status_code == OK_RESPONSE
    assert j["res"] == expected


# ---------------------------------------------------------------------------
# TEST 11: test_server_time
#   Test the weekday calculation of server_time function: It returns a string that
#       includes a weekday ("Mon", "Tue"...) that is calculated based on the result
#       of get_network_time. We want to know it calculates the weekday correctly,
#       without waiting 1 day between tests. You need to stub get_network_time.
#       In this implementation, test the function main.server_time() directly,
#           not through the TestClient.
#   Use parameters, a single function should result in 7 tests, one for
#       each of the 7 days of the week.
#   Hint: You will need to use:
#       - "parametrize" with the test and the expected result,
#       - "monkeypatch" to overwrite the function in "extra" that provides time info
#       - "pytest.raises" because the function works by throwing a 203 exception
#   203: Non-Authoritative Information
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("expected_weekday", [datetime.datetime.now() + datetime.timedelta(days=i) for i in range(7)])
def test_server_time(expected_weekday, monkeypatch):
    monkeypatch.setattr(extra, "get_network_time", lambda: expected_weekday)

    with pytest.raises(fastapi.HTTPException) as http_exception:
        main.server_time()

    server_time_exception = http_exception.value
    assert server_time_exception.status_code == http_status.HTTP_203_NON_AUTHORITATIVE_INFORMATION
    assert server_time_exception.detail.startswith(expected_weekday.strftime("%a"))


# ---------------------------------------------------------------------------
# TEST 12: test_server_time_client
#   Test the weekday calculation of the "/time" REST call. You still need to
#       stub get_network_time.
#       In this implementation, test through the TestClient for easier code flow,
#           not by calling main.server_time() directly.
#
#   Instead of parametrizing, use metamorphic tests: For today's date (you don't need
#       to know which date or day it is), test that whatever weekday it received, the
#       following days (try the next 100) are of a weekday that is appropriate.
#   Hint: You will need to use:
#       - "monkeypatch" to overwrite the function in "extra" that provides time info
#       - fastapi's "TestClient" to run the REST API via a client and avoid the exception.
#       - a large loop and a smart way to check the weekday
#   203: Non-Authoritative Information
# ---------------------------------------------------------------------------
def test_server_time_client(monkeypatch):
    for days_counter in range(100):
        test_date = datetime.datetime.now() + datetime.timedelta(days=days_counter)
        monkeypatch.setattr(extra, "get_network_time", lambda: test_date)
        server_time_response = client.get("/time")
        assert http_status.HTTP_203_NON_AUTHORITATIVE_INFORMATION == server_time_response.status_code
        assert server_time_response.json()['detail'].startswith((test_date.strftime("%a")))


# ---------------------------------------------------------------------------
# TEST 13: test_storage_db
#   Test the DB update function of the storage function: StateMachine.add_string()
#   You are looking to test that when "/storage/add?string=qwert" is called,
#       StateMachine.add_string() calls extra.update_db() correctly.
#   Checking that "/storage/query?index=1" is not enough, and it doesn't check
#       the extra.update_db() call.
#   Hint: You will need to use:
#       - "monkeypatch" to overwrite the update_db function in "extra".
#       - fastapi's "TestClient" to run the REST API via a client (it keeps the session alive).
#       - A function you invent that will mock update_db and update a flag for pass/fail (can be global)
# ---------------------------------------------------------------------------

update_db_called = False


def test_storage_db(monkeypatch):
    test_word = "qwert"
    monkeypatch.setattr(extra, "update_db", lambda a_db, value: mock_update_db(a_db, value))
    add_string_response = client.get(f"/storage/add?string={test_word}")
    assert add_string_response.status_code == OK_RESPONSE
    assert update_db_called  # Check extra.update_db() was called
    get_index_response = client.get("/storage/query?index=1")
    assert get_index_response.status_code == OK_RESPONSE


def mock_update_db(a_db, value):
    global update_db_called
    update_db_called = True


# ---------------------------------------------------------------------------
# TEST 14: Test the storage functions until it reaches 100% statement coverage.
#   That is, coverage of the "def storage" function and of all functions
#       within "class StateMachine" (lines 511-668).
#
#   Check coverage with the command "coverage run -m pytest", you can look at the functions
#       mentioned above with the HTML report: ("coverage html" and ".\htmlcov\index.html")
#   Hint: It is recommended to use:
#       - fastapi's "TestClient" to run the REST API via a client (it keeps the session alive).
# ---------------------------------------------------------------------------
def test_storage():
    # Standby -> get state
    apply_command(GET_STATE_COMMAND)
    check_expected_state(STANDBY_STATE)

    # Standby -> Input
    add_string_command()
    check_expected_state(INPUT_STATE)

    # Input -> clear -> stop -> Standby
    apply_command(CLEAR_COMMAND)
    apply_command(STOP_COMMAND)
    check_expected_state(STANDBY_STATE)

    # Standby -> Input -> Error -> sorry -> Query -> valid query
    move_to_error()
    check_expected_state(ERROR_STATE)
    apply_command(SORRY_COMMAND)
    check_expected_state(QUERY_STATE)
    query_index_command(1)

    # Query -> invalid query -> Error -> Query -> stop
    query_index_command(9)
    check_expected_state(ERROR_STATE)
    apply_command(SORRY_COMMAND)
    check_expected_state(QUERY_STATE)
    apply_command(STOP_COMMAND)
    check_expected_state(STANDBY_STATE)

    # Standby -> Input -> Error -> sorry -> Query -> clear -> Input
    move_to_error()
    check_expected_state(ERROR_STATE)
    apply_command(SORRY_COMMAND)
    check_expected_state(QUERY_STATE)
    apply_command(CLEAR_COMMAND)
    check_expected_state(INPUT_STATE)

    # Input -> Error -> clear -> Input
    move_to_error()
    check_expected_state(ERROR_STATE)
    apply_command(CLEAR_COMMAND)
    check_expected_state(INPUT_STATE)

    # Input -> Error -> stop -> Standby
    move_to_error()
    check_expected_state(ERROR_STATE)
    apply_command(STOP_COMMAND)
    check_expected_state(STANDBY_STATE)


def apply_command(command):
    command_response = client.get(f"/storage/{command}")
    assert command_response.status_code == OK_RESPONSE


def add_string_command(test_word="test_word"):
    add_string_response = client.get(f"/storage/add?string={test_word}")
    assert add_string_response.status_code == OK_RESPONSE


def query_index_command(index):
    query_response = client.get(f"/storage/query?index={str(index)}")
    assert query_response.status_code == OK_RESPONSE


def move_to_error():
    for i in range(6):
        add_string_response = client.get(f"/storage/add?string={str(i)}")
        assert add_string_response.status_code == OK_RESPONSE


def check_expected_state(state):
    get_state_response = client.get(f"/storage/state")
    assert get_state_response.json()['res'].startswith(f"State: {state}")