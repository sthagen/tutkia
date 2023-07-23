"""Explore (Finnish: tutkia) ticket system trees. - application programming interface."""
import argparse
import inspect
import os
from typing import Union, no_type_check

from atlassian import Jira  # type: ignore
from tutkia import (
    APP_ALIAS,
    APP_NAME,
    APP_VERSION,
    ENCODING,
    LOG_SEPARATOR,
    QUIET,
    TS_FORMAT_PAYLOADS,
    log,
)

COMMA = ','
FIELDS = 'fields'
NAME = 'name'
NONE = 'None'
PERCENT = 'percent'
SEMI = ';'
VALUE = 'value'
CONN_SERVER = os.getenv(f'{APP_ALIAS}_SERVER', '').rstrip(SEMI)
CONN_USER = os.getenv(f'{APP_ALIAS}_USER', '')
CONN_TOKEN = os.getenv(f'{APP_ALIAS}_TOKEN', '')


@no_type_check
def extract(per, seq, slot: int):
    """Extract per functors from sequence at slot."""
    return [[extractor.__name__, extractor(seq[slot][FIELDS])] for extractor in per]


def cf(n: int) -> str:
    """Shorthand for data interpolation."""
    return f'customfield_{n}'


CF = {
    'Acceptance Criteria': cf(11000),
    'Customer Project Code': cf(13601),
    'Department': cf(11616),
    'ORG Engineering Service': cf(13801),
    'Lifecycle Stage': cf(13701),
    'Start date': cf(13500),
    'ORG customers': cf(11621),
    'ORG Product': cf(12317),
}

FNI = inspect.currentframe


@no_type_check
def unwrap(d, sk, default: Union[int, str] = NONE, pk=None):
    if pk is None:
        pk = FNI().f_back.f_code.co_name
    data = d.get(pk, None)
    if data is None:
        return default
    return data.get(sk, default) if d[pk] else default


@no_type_check
def summary(d):
    return d[FNI().f_code.co_name]


@no_type_check
def issuetype(d):
    return unwrap(d, NAME)


@no_type_check
def priority(d):
    return unwrap(d, NAME)


@no_type_check
def status(d):
    return unwrap(d, NAME)


@no_type_check
def resolution(d):
    return unwrap(d, NAME)


@no_type_check
def reporter(d):
    return unwrap(d, NAME)


@no_type_check
def assignee(d):
    return unwrap(d, NAME)


@no_type_check
def department(d):
    return unwrap(d, VALUE, pk=CF['Department'])


@no_type_check
def org_eng_service(d):
    return unwrap(d, VALUE, pk=CF['ORG Engineering Service'])


@no_type_check
def life_cycle_stage(d):
    return unwrap(d, VALUE, pk=CF['Lifecycle Stage'])


@no_type_check
def org_customer(d):
    return unwrap(d, VALUE, pk=CF['ORG customers'])


@no_type_check
def customer_project_code(d):
    return d.get(CF['Customer Project Code'], NONE)


@no_type_check
def org_product(d):
    return unwrap(d, VALUE, pk=CF['ORG Product'])


@no_type_check
def created(d):
    return d[FNI().f_code.co_name]


@no_type_check
def start_date(d):
    return d.get(CF['Start date'], NONE)


@no_type_check
def updated(d):
    return d[FNI().f_code.co_name]


@no_type_check
def due_date(d):
    return d.get('duedate', NONE)


@no_type_check
def aggregateprogress(d):
    return unwrap(d, PERCENT)


@no_type_check
def labels(d):
    return d[FNI().f_code.co_name]


@no_type_check
def aggregatetimeoriginalestimate(d):
    return d[FNI().f_code.co_name]


@no_type_check
def timeoriginalestimate(d):
    return d[FNI().f_code.co_name]


@no_type_check
def timeestimate(d):
    return d[FNI().f_code.co_name]


@no_type_check
def original_estimate_seconds(d):
    return unwrap(d, 'originalEstimateSeconds', default=0, pk='timetracking')


@no_type_check
def remaining_estimate_seconds(d):
    return unwrap(d, 'remainingEstimateSeconds', default=0, pk='timetracking')


@no_type_check
def time_spent_seconds(d):
    return unwrap(d, 'timeSpentSeconds', default=0, pk='timetracking')


@no_type_check
def process(options: argparse.Namespace):
    """Process the command line request."""
    global CONN_TOKEN
    query = options.query
    jira = Jira(url=CONN_SERVER, username=CONN_USER, password=CONN_TOKEN, cloud=False)
    CONN_TOKEN = '*' * 42  # overwrite after use

    try:
        issues = jira.jql(query)
    except Exception as err:  # noqa
        print(err)
        return 1

    retrieved = len(issues['issues'])
    total = issues['total']
    print(f'Retrieved {retrieved} of {total} matching issues')
    page_first = issues['startAt']
    page_max = issues['maxResults']
    max_page_frame = (page_first, page_max - 1)
    print(f'Current maximal page frame is {max_page_frame}')
    eff_page_frame = max_page_frame if total > page_max else (page_first, total - 1)
    print(f'Current effective page frame is {eff_page_frame}')

    try:
        expand_dims = issues['expand'].split(COMMA)
    except KeyError:
        print(f'No issues match query ({query})')
        print(f'- received response: {issues}')
        return 0

    print(f'Expanded dimensions is {tuple(str(v) for v in expand_dims)}')
    issue_seq = issues['issues']
    keys_present = [issue['key'] for issue in issue_seq]
    print(f'Keys present: {tuple(str(v) for v in keys_present)}')

    # list(issues['issues'][0]['fields'].keys())
    via = (
        summary,
        issuetype,
        priority,
        status,
        resolution,
        reporter,
        assignee,
        department,
        org_eng_service,
        life_cycle_stage,
        org_customer,
        customer_project_code,
        org_product,
        created,
        start_date,
        updated,
        due_date,
        aggregateprogress,
        labels,
        aggregatetimeoriginalestimate,
        timeoriginalestimate,
        timeestimate,
        original_estimate_seconds,
        remaining_estimate_seconds,
        time_spent_seconds,
    )

    print()
    for slot, key in enumerate(keys_present):
        pairs = extract(via, issue_seq, slot)
        print(f'{slot + 1}. {key}')
        for k, v in pairs:
            print(f'  - {k :42s}: {v}')
        print()
    return 1
