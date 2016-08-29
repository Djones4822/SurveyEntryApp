#!/usr/bin/env python

from time import localtime, strftime
import cx_Oracle

GET_QUESTION_QUERY = """
select t1.id, t1.text, t2.q_order
from davidj.rs_question t1,
davidj.rs_question_order t2,
davidj.rs_survey t3
where t1.id = t2.question_id
and t3.id =t2.survey_id
and t3.id = :survey_id
order by t2.q_order"""

GET_AVAIL_RESPONSE_QUERY = """
select t1.text, t1.id
from rs_response_choice t1
where t1.question_id = :qid
order by t1.ANSWER_ORDER
"""

GET_QTYPE_QUERY = """
select t1.name, t2.name
from rs_question_type t1,
rs_question_type_xref t2
where t1.name = t2.question_type_id and t1.question_id = :qid
"""

GET_SURVEY_ADMINS_QUERY = """
select t1.NAME, t2.date_taken, t2.date_entered, t2.id, t2.survey_id, t2.last_updated, t2.respondent_id
from RS_SURVEY_RESPONSE t2, rs_survey t1
where t1.id = t2.survey_id and respondent_id = :id order by date_taken desc
"""

INSERT_RESPONSES_QUERY = """
INSERT INTO RS_RESPONSE VALUES (:1, :2, :3, :4)
"""

INSERT_SURVEY_ADMIN_QUERY = """
INSERT INTO RS_SURVEY_RESPONSE (ID, SURVEY_ID, RESPONDENT_ID, DATE_TAKEN, DATE_ENTERED)
VALUES (:sr_id, :survey_id, :respondent_id, to_date( :dt, 'MM/DD/YYYY'), to_timestamp( :ts, 'YYYY-MM-DD HH24:MI:SS'))
"""

GET_RESPONDENTS_QUERY = """
select distinct t1.ID, t1.name, t1.Enrolled_District, t1.cohort, t2.name
from rs_respondent t1, rs_respondent_type_xref t2
where t1.respondent_type_id = t2.id
and lower(t1.name) like '%' || :part || '%'
"""

GET_AVAILABLE_SURVEYS = """
SELECT t3.survey_id, t2.name, t2.description
from rs_respondent t1,
rs_survey t2,
RS_AVAILABLE_SURVEYS t3
where t3.respondent_type_id = t1.respondent_type_id and t3.survey_id = t2.id and t1.id = :id
"""

GET_GIVEN_ANSWERS = """
SELECT t1.question_id, t1.answer, t3.q_order from rs_response t1, rs_survey_response t2, rs_question_order t3
where t1.survey_response_id = :admin_id
and t1.survey_response_id = t2.id
and t2.survey_id = t3.survey_id
and t1.question_id = t3.question_id
"""

def connect(name, pw, domain):
    '''
    Connection process. Takes a given username and password and returns a connection object.
    :param name: string, the username of the user connecting to the database
    :param pw: string, the password of the user connecting to the database
    :param domain: string, the domain of the Oracle DB
    :return: cx_Oracle connection object to be used throughout the program
    '''
    try:
        con = cx_Oracle.connect('{}/{}@{}'.format(name, pw, domain))
    except cx_Oracle.DatabaseError as e:
        error, = e.args
        if error.code == 1017:
            print('Please check your credentials and domain.'.format(name, pw))
            return -2
        # sys.exit()?
        else:
            print('Database connection error: {}'.format(e))
            return -1
    return con


def get_survey_questions(con, survey_id):
    '''
    Takes a given survey ID and produces a list of tuples containing the question ID, the question text, and the order
    the question falls in (index+1).
    :param con: cx_Oracle connection object
    :param survey_id: integer - the survey id [1,6]
    :return: a list of tuples containing the question id, the question text, and the relative question order.
    '''
    questions_cursor = con.cursor()
    query = GET_QUESTION_QUERY
    questions_cursor.prepare(query)
    questions_cursor.execute(None, {'survey_id': survey_id})
    questions = questions_cursor.fetchall()
    questions_cursor.close()
    return questions


def get_question_responses(con, qid):
    '''
    Takes the connection and question ID and produces a list of strings containing the corresponding results, only to be
    used when the question type is neither "short_string" or "long_string"
    :param con: connection object from cx_Oracle
    :param qid: question ID corresponding to a response-containing question. Only to be used after get_question_type()
    :return: returns a list of tuples containing the id and text string for each of the available answers
    '''
    query = GET_AVAIL_RESPONSE_QUERY
    responses_cursor = con.cursor()
    responses_cursor.prepare(query)
    responses_cursor.execute(None, {'qid': qid})
    responses = [(resp[1],resp[0]) for resp in responses_cursor.fetchall()]
    responses_cursor.close()
    return responses


def get_question_type(con, qid):
    '''
    Takes the connection and the question ID and produces the question type out of the list: short_string, single_choice,
    table_single_choice, long_string, table_multiple_choice, multiple_choice
    :param con: connection object from cx_Oracle
    :param qid: the question ID
    :return: a tuple containing the type id and the string name of the type (in that order)
    '''
    query = GET_QTYPE_QUERY
    qtype_cursor = con.cursor()
    qtype_cursor.prepare(query)
    qtype_cursor.execute(None, {'qid': qid})
    qtype = qtype_cursor.fetchall()[0]
    qtype_cursor.close()
    return qtype


def insert_responses(con, row_list):
    '''
    Takes the connection and the list of answer lists compiled through the data entry process. Each row should be a specific
    format of [survey_response_id, question_id, respondent_id, answer_string].
    :param con: connection object created by cx_Oracle
    :param row_list: list of lists/tuples - each question response is a list contained within the overall list to be passed.
                    This list is iterated through and each is inserted into the database. Only one call per survey entry only.
    :return: None
    '''
    query = INSERT_RESPONSES_QUERY
    insert_cursor = con.cursor()
    insert_cursor.prepare(query)
    try:
        insert_cursor.executemany(None, row_list)
        con.commit()
    except:
        con.rollback()
        return 1
    insert_cursor.close()
    return None


def insert_new_survey_response(con, survey_id, respondent_id, date_taken):
    '''
    Takes the connection object, the id # of the survey, the id # of the student and the date the survey was originally
    taken and updates the database to reflect the new survey while returning the ID of that survey to be included with
    the responses.
    :param con: the connection object created by cx_Oracle
    :param survey_id: the id of the survey, in the range [1,6]
    :param respondent_id: the id of the respondent
    :param date_taken: the date the survey was originally taken, must be in MM-DD-YYYY format
    :return: the id of the survey administration
    '''
    max_query = 'select max(id) from rs_survey_response'
    cursor = con.cursor()
    cursor.execute(max_query)
    ids = cursor.fetchall()
    returned = ids[0][0]
    if returned:
        new_id = returned+1
    else:
        new_id = 1

    data = [new_id, survey_id, respondent_id, date_taken, format_timestamp()]
    #print(data)
    cursor.prepare(INSERT_SURVEY_ADMIN_QUERY)
    cursor.execute(None, {"sr_id":data[0], "survey_id":data[1], "respondent_id":data[2], "dt":data[3], "ts":data[4]})
    con.commit()
    cursor.close()
    return new_id


def format_timestamp():
    '''
    Generates a timestamp in Oracle format
    :return: the timestamp in YYYY-MM-DD HH24:MM:SS time
    '''
    #'YYYY-MM-DD HH24:MI:SS.FF'
    time = strftime("%Y-%m-%d %H:%M:%S", localtime())
    return time


def search_for_names(con, str_name):
    '''
    Takes the connection and a string and searches the table RS_RESPONDENT for any rows that contains the split elements
    of the input. For example, 'David Jones' searches for anyone with 'david' or 'jones' in the "name" field and returns
    the following rows in order: ID, Enrolled_District, Cohort, Respondent Type.
    :param con: connection object created by cx_Oracle
    :param str_name: the name of the respondent being searched for
    :return: returns a list with all rows (as tuples) retrieved in the result set
    '''
    name = str_name.lower()
    #print(name_parts)
    cursor = con.cursor()
    query = GET_RESPONDENTS_QUERY
    cursor.prepare(query)
    cursor.execute(None, {'part':name})
    results = cursor.fetchall()
    cursor.close()
    return results


def get_taken_surveys(con, resp_id):
    """
    Takes the connection and the id of a respondent and searches for all survey administrations. Returns the rows with
    the date the survey was originally taken and the name of the survey.
    :param con: connection object created by cx_Oracle
    :param resp_id: the id # of the respondent
    :return: a list of all returned rows as tuples
    """
    cursor = con.cursor()
    cursor.prepare(GET_SURVEY_ADMINS_QUERY)
    cursor.execute(None, {'id':resp_id})
    results = cursor.fetchall()
    results = [res for res in results]
    cursor.close()
    return results

def get_available_surveys(con, resp_id):
    """
    Takes a cx_oracle connection and the id of the respondent and returns the name and description of the surveys available
    to them.
    :param con: cx_oracle connection
    :param resp_id: integer id number of the respondent
    :return: list of tuples containing survey info: (name, description)
    """
    cursor = con.cursor()
    cursor.prepare(GET_AVAILABLE_SURVEYS)
    cursor.execute(None, {'id':resp_id})
    results = cursor.fetchall()
    results = [res for res in results]
    cursor.close()
    return results

def get_survey_id(con, survey_name):
    cursor = con.cursor()
    query = "select id from rs_survey where name = :name"
    cursor.prepare(query)
    cursor.execute(None, {'name':survey_name})
    results = cursor.fetchall()
    result = [res for res in results][0][0]
    cursor.close()
    return result

def get_survey_name(con, survey_id):
    cursor = con.cursor()
    query = 'Select name from rs_survey where id = :id'
    cursor.prepare(query)
    cursor.execute(None, {'id':survey_id})
    results = cursor.fetchall()
    cursor.close()
    return [res for res in results][0][0]

def get_student_name_from_id(con, resp_id):
    cursor=con.cursor()
    query = 'SELECT name from rs_respondent where id = :id'
    cursor.prepare(query)
    cursor.execute(None, {'id':resp_id})
    result = cursor.fetchall()[0][0]
    cursor.close()
    return result

def get_given_answers(con, admin_id):
    '''
    returns a the raw output of the query
    :param con:
    :param admin_id:
    :return: a list of tuples}
    '''
    cursor = con.cursor()
    query = GET_GIVEN_ANSWERS
    cursor.prepare(query)
    cursor.execute(None, {'admin_id':admin_id})
    result = cursor.fetchall()
    cursor.close()
    return result

def delete_old_responses(con, admin_id):
    cursor = con.cursor()
    query = 'DELETE FROM rs_response where SURVEY_RESPONSE_ID = :admin_id'
    cursor.prepare(query)
    try:
        cursor.execute(None, {'admin_id':admin_id})
        con.commit()
    except:
        con.rollback()
        return -1
    cursor.close()
    return None

def update_survey_response(con, admin_id):
    cursor = con.cursor()
    ts = format_timestamp()
    #print(ts)
    query = 'UPDATE rs_survey_response SET last_updated = to_timestamp( :ts, \'YYYY-MM-DD HH24:MI:SS\')WHERE id =:admin_id'
    cursor.prepare(query)
    try:
        cursor.execute(None, {'ts': ts, 'admin_id':admin_id})
        con.commit()
    except:
        con.rollback()

        return -1
    cursor.close()
    return None

def get_existing_respondents(con, resp_type):
    cursor = con.cursor()
    query = 'SELECT name, id, enrolled_district from rs_respondent where RESPONDENT_TYPE_ID = :id'
    cursor.prepare(query)
    cursor.execute(None, {'id':resp_type})
    results = cursor.fetchall()
    results = [res for res in results]
    cursor.close()
    return results

def get_given_students(con, id):
    cursor = con.cursor()
    query = 'SELECT answer from rs_response where respondent_id = :id and question_id = 97'
    cursor.prepare(query)
    cursor.execute(None, {'id':id})
    results = cursor.fetchall()
    results = [res[0] for res in results]
    cursor.close()
    return results

def insert_respondent(con, name, resp_type):
    cursor = con.cursor()
    new_id = cursor.execute('SELECT MAX(ID) FROM RS_RESPONDENT').fetchall()[0][0] + 1
    print(new_id, name, resp_type)
    query = 'INSERT INTO RS_RESPONDENT (ID, NAME, RESPONDENT_TYPE_ID) VALUES(:id, :name, :type)'
    cursor.prepare(query)
    try:
        cursor.execute(None, {'id':new_id, 'name':name, 'type':resp_type})
        con.commit()
        cursor.close()
        return None
    except:
        con.rollback()
        cursor.close()
        return -1

def get_student_district(con, id):
    cursor = con.cursor()
    query = 'select enrolled_district from rs_respondent where id = :id'
    cursor.prepare(query)
    cursor.execute(None, {'id':id})
    result = cursor.fetchall()[0][0]
    cursor.close()
    return result

def update_district(con, respondent_id, district):
    cursor = con.cursor()
    query = 'UPDATE RS_RESPONDENT SET ENROLLED_DISTRICT = :district WHERE ID = :id'
    cursor.prepare(query)
    try:
        cursor.execute(None, {'id':respondent_id, 'district':district})
        con.commit()
        cursor.close()
        return None
    except:
        cursor.close()
        return -1