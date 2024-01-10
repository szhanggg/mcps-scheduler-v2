import psycopg2
from flask import Flask, render_template
app = Flask(__name__)

conn = psycopg2.connect(
    "dbname=postgres user=postgres password=supabasePassword123@ host=db.lgiguvakxsdbpipdoxdn.supabase.co")
cur = conn.cursor()

TEST_DATA = [
    {
        "period": 1,
        "name": "Science",
        "teacher": "Mr. Smith",
        "room": "123",
        "students": [
                "John Doe",
                "Jane Doe",
                "Bob Smith"
        ]

    },
    {
        "period": 2,
        "name": "Math",
        "teacher": "Mr. John",
        "room": "456",
        "students": [
                "Bob Doe",
                "Janet Smith",
                "Rob Johnson"
        ]

    }
]


@app.route('/')
def index():
    return render_template('index.html', logged_in=True, classes=TEST_DATA, error="Invalid Login")


@app.route('/directory')
def directory():
    return render_template('directory.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=4999)
