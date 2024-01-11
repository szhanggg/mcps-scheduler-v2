import psycopg2
from psycopg2 import pool
from studentvue import StudentVue
from flask import Flask, render_template, request
app = Flask(__name__)

db_pool = psycopg2.pool.SimpleConnectionPool(1, 20, dbname="postgres", user="postgres", password="supabasePassword123@", host="db.lgiguvakxsdbpipdoxdn.supabase.co")

def getData(sv, sid):
    data = {}
    data['sid'] = sid

    schedule = sv.get_schedule(1)
    if "RT_ERROR" in schedule.keys():
        return {"error": "Invalid Credentials"}

    studentClassSchedule = schedule['StudentClassSchedule']

    classLists = studentClassSchedule['ClassLists']
    
    classListing = classLists['ClassListing']

    data['classes'] = []

    school_info = sv.get_school_info()
    schoolName = school_info['StudentSchoolInfoListing']['@School']

    for i in classListing:
        curClass = {}
        curClass['name'] = i['@CourseTitle']
        curClass['period'] = str(i['@Period'])
        curClass['room'] = str(i['@RoomName'])
        curClass['teacher'] = i['@Teacher']
        curClass['school'] = schoolName

        data['classes'].append(curClass)
     
    sinfo = sv.get_student_info()
    studentInfo = sinfo['StudentInfo']
    sname = studentInfo['FormattedName']['$']
    nname = studentInfo['NickName']['$']

    data['sname'] = sname
    data['nname'] = nname

    data = updateData(data)

    return data

def updateData(data):
    conn = db_pool.getconn()
    cur = conn.cursor()
    newData = data
    cur.execute("SELECT id, sname, classes FROM students WHERE id = %s", (data['sid'],))
    found = cur.fetchone()
    student = None
    if not found:
        cur.execute("INSERT INTO students (id, sname, classes) VALUES (%s, %s, %s)", (data['sid'], data['sname'], formatClassList(data['classes'])))
        student = (int(data['sid']), data['sname'], formatClassList(data['classes']))
    else:
        student = found 
    
    if formatClassList(data['classes']) != student[2]:
        for i in unformatClassList(student[2]):
            deleteStudentFromClass(data['sname'], i, conn, cur)
        
        cur.execute("UPDATE students SET classes = %s WHERE id = %s", (formatClassList(data['classes']), data['sid']))

    for i in data['classes']:
        students = addStudentToClass(data['sname'], i, conn, cur)
        newData['classes'][newData['classes'].index(i)]['students'] = unformatStudentList(students)
    
    conn.commit()
    cur.close()
    db_pool.putconn(conn)
    return newData

def formatClassList(classes):
    classList = []
    for i in classes:
        classList.append(i['name'] + '|~|' + i['period'] + '|~|' + i['room'] + '|~|' + i['teacher'] + '|~|' + i['school'])
    return '~|~'.join(classList)

def unformatClassList(classes):
    classList = []
    for i in classes.split('~|~'):
        classInfo = i.split('|~|')
        classList.append({'name': classInfo[0], 'period': classInfo[1], 'room': classInfo[2], 'teacher': classInfo[3], 'school': classInfo[4]})
    return classList

def formatStudentList(students):
    return '~|~'.join(students)

def unformatStudentList(students):
    return students.split('~|~')

def deleteStudentFromClass(sname, classInfo, conn, cur):
    cur.execute("SELECT students FROM classes WHERE name = %s AND period = %s AND room = %s AND teacher = %s AND school = %s", (classInfo['name'], classInfo['period'], classInfo['room'], classInfo['teacher'], classInfo['school']))
    found = cur.fetchone()
    if not found:
        cur.execute("INSERT INTO classes (name, period, room, teacher, students, school) VALUES (%s, %s, %s, %s, %s, %s)", (classInfo['name'], classInfo['period'], classInfo['room'], classInfo['teacher'], sname, classInfo['school']))
        conn.commit()
        return
    
    students = unformatStudentList(found[0])

    if sname in students:
        students.remove(sname)
        cur.execute("UPDATE classes SET students = %s WHERE name = %s AND period = %s AND room = %s AND teacher = %s AND school = %s", (formatStudentList(students), classInfo['name'], classInfo['period'], classInfo['room'], classInfo['teacher'], classInfo['school']))
        conn.commit()
        return

def addStudentToClass(sname, classInfo, conn, cur):
    cur.execute("SELECT students FROM classes WHERE name = %s AND period = %s AND room = %s AND teacher = %s AND school = %s", (classInfo['name'], classInfo['period'], classInfo['room'], classInfo['teacher'], classInfo['school']))
    found = cur.fetchone()
    if not found:
        cur.execute("INSERT INTO classes (name, period, room, teacher, students, school) VALUES (%s, %s, %s, %s, %s, %s)", (classInfo['name'], classInfo['period'], classInfo['room'], classInfo['teacher'], sname, classInfo['school']))
        conn.commit()
        return sname

    students = unformatStudentList(found[0])

    if sname not in students:
        students.append(sname)
        formatted_students = formatStudentList(students)
        cur.execute("UPDATE classes SET students = %s WHERE name = %s AND period = %s AND room = %s AND teacher = %s AND school = %s", (formatted_students, classInfo['name'], classInfo['period'], classInfo['room'], classInfo['teacher'], classInfo['school']))
        conn.commit()
        return formatted_students
    
    return formatStudentList(students)

@app.route('/')
def index():
    return render_template('index.html', logged_in=False)


@app.route('/directory')
def directory():
    # Get a list of all schools
    conn = db_pool.getconn()
    cur = conn.cursor()
    # Get all the unique school attributes from the classes table
    cur.execute("SELECT DISTINCT school FROM classes")
    schools = cur.fetchall()
    # Covnert to list of strings
    schools = [i[0] for i in schools]
    cur.close()
    db_pool.putconn(conn)
    return render_template('directory.html', schools=schools)

@app.route('/getClassList')
def getClassList():
    school = request.args.get('school')
    conn = db_pool.getconn()
    cur = conn.cursor()
    cur.execute("SELECT name, period, room, teacher FROM classes WHERE school = %s", (school,))
    classes = cur.fetchall()
    cur.close()
    db_pool.putconn(conn)
    # return json with classes
    return {'classes': classes}

@app.route('/login', methods=['POST'])
def login():

    login_data = request.get_json()
    sid = login_data['sid']
    password = login_data['password']

    sv = StudentVue(sid, password, 'md-mcps-psv.edupoint.com')

    data = getData(sv, sid)
    if("error" in data.keys()):
        return render_template('index.html', logged_in=False, error=data['error'])

    return render_template('index.html', logged_in=True, data=data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4999)
