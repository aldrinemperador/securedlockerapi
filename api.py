import flask
from flask import request, jsonify, abort
# from flask_cors import CORS
import sqlite3
import json
from datetime import datetime, timedelta
import time
import serial

app = flask.Flask(__name__)
app.config["DEBUG"] = True
# CORS(app)

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


@app.route('/', methods=['GET'])
def home():
    return '''<h1>Secured Locker Application API</h1>
<p>A prototype API for .</p>'''


@app.route('/api/v1/students/all', methods=['GET'])
def get_students_all():
    conn = sqlite3.connect('securedlockerappdb.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_students = cur.execute('SELECT * FROM students;').fetchall()

    return jsonify(all_students)

@app.route('/api/v1/students/single', methods=['GET'])
def get_student():
    conn = sqlite3.connect('securedlockerappdb.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()

    studentId = request.args.get("studentId")
    student = cur.execute("SELECT * FROM students WHERE StudentID='" + studentId + "'").fetchall()

    return jsonify(student)

@app.route('/api/v1/courses/all', methods=['GET'])
def get_all_courses():
    conn = sqlite3.connect('securedlockerappdb.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_courses = cur.execute("SELECT * FROM Courses").fetchall()

    return jsonify(all_courses)


@app.route('/api/v1/lockers/all', methods=['GET'])
def get_lockers_all():
    conn = sqlite3.connect('securedlockerappdb.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_lockers = cur.execute('SELECT * FROM Lockers;').fetchall()

    return jsonify(all_lockers)

@app.route('/api/v1/lockers/all-subscriptions', methods=['GET'])
def get_lockers_subscriptions():
    conn = sqlite3.connect('securedlockerappdb.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    all_subscriptions = cur.execute('SELECT * FROM LockerSubscription WHERE DateTimeEnd IS NULL').fetchall()

    lockerSubscriptions = []
    if len(all_subscriptions) > 0:
        for items in all_subscriptions:
            lockerSubscriptions.append({ "studentId": items['StudentID'], "lockerId": items['LockerID'], "timeRemaining": getTimeRemaining(items['SubscriptionDateTime'], items['Time']) })

    print(lockerSubscriptions)
    return jsonify(lockerSubscriptions)

def getTimeRemaining(subscriptionDateTime, time):
    dateNow  = datetime.now()
    newTime = int(time)
    subscriptionEndDateTime = (datetime.strptime(subscriptionDateTime, '%m/%d/%Y %H:%M:%S') + timedelta(hours=newTime)).strftime('%m/%d/%Y %H:%M:%S') 
    duration = datetime.strptime(subscriptionEndDateTime, '%m/%d/%Y %H:%M:%S') - dateNow
    duration_in_sec = duration.total_seconds()
    #hours = divmod(duration_in_sec, 60)[0]

    return duration_in_sec

@app.route('/api/v1/lockers/user-subscription', methods=['GET'])
def get_user_locker_subscription():
    studentId = request.args.get("studentId")
    lockerId = request.args.get("lockerId")
    conn = sqlite3.connect('securedlockerappdb.db')
    conn.row_factory = dict_factory
    cur = conn.cursor()
    locker_subscription = cur.execute("SELECT * FROM LockerSubscription WHERE DateTimeEnd IS NULL AND LockerID=" + lockerId).fetchone()
    user_subscription = cur.execute("SELECT * FROM LockerSubscription WHERE DateTimeEnd IS NULL AND StudentID='" + studentId + "'").fetchone()

    print(locker_subscription)
    api_response = ""
    if locker_subscription != None and len(locker_subscription) > 0:
        if locker_subscription['StudentID'] == studentId:
            api_response = ({ "success": True, "studentId": locker_subscription['StudentID'], "lockerId": locker_subscription['LockerID'], "message": None, "errorCode": 0 })
        else:
            api_response = ({ "success": False, "studentId": None, "lockerId": None, "message": "Invalid user.", "errorCode": 101 })
    else:
        if user_subscription != None and len(user_subscription) > 0:
            api_response = ({ "success": False, "studentId": None, "lockerId": None, "message": "You're already subscribed to other locker slot.", "errorCode": 102 })
        else:
            api_response = ({ "success": False, "studentId": None, "lockerId": None, "message": "Locker is available for subscription.", "errorCode": 103 })

    print(api_response)
    return jsonify(api_response)


@app.route('/api/v1/lockers/subscribe', methods=['GET'])
def subscribe_locker():
    studentId = request.args.get("studentId")
    lockerId = request.args.get("lockerId")
    billAccepted = request.args.get("billAccepted")
    time = request.args.get("time")
    date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    print(date_time)

    conn = sqlite3.connect('securedlockerappdb.db')

    conn.execute("INSERT INTO LockerSubscription (StudentID,LockerID,SubscriptionDateTime,Price,Time) VALUES (" + "'" + studentId + "'," + lockerId +",'" + date_time + "'," + billAccepted + "," + time + ")")
    #values = (studentId, lockerId, datetime.datetime.now(), billAccepted, time)
    #conn.execute(query, values)
    conn.commit()

    #gets data
    conn.row_factory = dict_factory
    cur = conn.cursor()
    lockers = cur.execute("SELECT * FROM Lockers WHERE LockerID=" + lockerId).fetchone()

    #Send SMS
    send_sms(lockers['LockerNo'], time, date_time)

    #conn.execute("INSERT INTO LockerSubscription (StudentID,LockerID,SubcriptionDateTime,Price,Time) VALUES (%s,%s,%s,%s,%s)")
    return jsonify({ 'success': True, 'lockerId': lockerId, 'time': 3 }), 201

def send_sms(lockerId, hrs, subscriptionDateTime): 
    expiryDateTime = (datetime.strptime(subscriptionDateTime, '%m/%d/%Y %H:%M:%S') + timedelta(hours=3)).strftime('%m/%d/%Y %H:%M:%S')  
    serial_data = "SMS001," + "+639165568927," + lockerId + "," + hrs + "," + expiryDateTime
    print(serial_data)
    try:
        arduino = serial.Serial("COM3",9600,timeout = 5)
    except:
        print("Please check the port") 

    rawdata = []
    count = 0

    time.sleep(1)
    while (count < 9):
        rawdata.append(str(arduino.readline()))
        count+=1

    print(rawdata)

    time.sleep(1)
    arduino.write(serial_data.encode())
    

@app.route('/api/v1/lockers/end-subscription', methods=['GET'])
def end_user_subscription():
    lockerId = request.args.get("lockerId")
    endedSubscription = request.args.get("hasEnded")
    conn = sqlite3.connect('securedlockerappdb.db')
    date_time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    print(endedSubscription)

    if (endedSubscription == 'false'):
        conn.execute("""UPDATE LockerSubscription SET DateTimeEnd = ? , isEndedSubscription=false WHERE LockerID = ? AND DateTimeEnd IS NULL""", (date_time, lockerId))
        conn.commit()
    else:
        conn.execute("""UPDATE LockerSubscription SET DateTimeEnd = ? , isEndedSubscription=true WHERE LockerID = ? AND DateTimeEnd IS NULL""", (date_time, lockerId))
        conn.commit()

    return jsonify({ "success": True })
# @app.route('/api/v1/students', methods=['GET'])
# def get_student():
#     query_parameters = request.args

#     id = query_parameters.get('id')
#     published = query_parameters.get('published')
#     author = query_parameters.get('author')

#     query = "SELECT * FROM books WHERE"
#     to_filter = []

#     if id:
#         query += ' id=? AND'
#         to_filter.append(id)
#     if published:
#         query += ' published=? AND'
#         to_filter.append(published)
#     if author:
#         query += ' author=? AND'
#         to_filter.append(author)
#     if not (id or published or author):
#         return page_not_found(404)

#     query = query[:-4] + ';'

#     conn = sqlite3.connect('books.db')
#     conn.row_factory = dict_factory
#     cur = conn.cursor()

#     results = cur.execute(query, to_filter).fetchall()

#     return jsonify(results)

@app.route('/api/v1/students/create', methods=['GET', 'POST'])
def create_student():
    # if request.method == 'OPTIONS':
    #         headers = {
    #             'Access-Control-Allow-Origin': '*',
    #             'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
    #             'Access-Control-Max-Age': 1000,
    #             'Access-Control-Allow-Headers': 'origin, x-csrftoken, content-type, accept',
    #         }
    #         return '', 200, headers
   # data = json.loads(request.data)

    # if not request.json or not 'title' in request.json:
    #     abort(400)

    
    #print(request.data)
    # query_parameters = request.get_json()
    # print(request.user_agent)
    studentId = request.args.get("studentId")
    studentName = request.args.get('studentName')
    studentCourse = request.args.get('course')
    contactNo = request.args.get('contactNo')
    #slotNo = request.args.get('slotNo')

    # studentId = query_parameters.get('studentId')
    # studentName = query_parameters.get('studentName')
    # studentCourse = query_parameters.get('course')
    # contactNo = query_parameters.get('contactNo')
    # slotNo = query_parameters.get('slotNo')
    # print()
    # studentId = query_parameters['studentId']
    # studentName = query_parameters['studentName']
    # studentCourse = query_parameters['course']
    # contactNo = query_parameters['contactNo']
    # slotNo = query_parameters['slotNo']

    # print(studentId)
    # print(studentName)
    # print(studentCourse)
    # print(contactNo)
    # print(slotNo)

    conn = sqlite3.connect('securedlockerappdb.db')

    conn.execute("INSERT INTO students (StudentID,StudentName,Course,ContactNo) VALUES (" + "'" + studentId + "','" + studentName +"','" + studentCourse + "','" + contactNo + "')")
    conn.commit()

    student = conn.execute("SELECT * FROM students WHERE StudentID='" + studentId + "'").fetchall()

    return jsonify({'user': student}), 201

@app.errorhandler(404)
def page_not_found(e):
    return "<h1>404</h1><p>The resource could not be found.</p>", 404


class LockerSubscriptions(object):
    """__init__() functions as the class constructor"""
    def __init__(self, studentId=None, lockerId=None, time=None):
        self.studentId = studentId
        self.lockerId = lockerId
        self.time = time

class GenericResponse(object):
    def __init__(self, success=None, studentId=None, lockerId=None, time=None, message=None):
        self.success = success
        self.studentId = studentId
        self.lockerId = lockerId
        self.time = time
        self.message = message

app.run()