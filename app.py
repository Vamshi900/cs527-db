import logging

from flask import Flask, request
import datetime
import decimal
import pymysql
import json
import config
from flask_cors import CORS
import time
# import psycopg2

app = Flask(__name__)

"""
CORS function is to avoid No 'Access-Control-Allow-Origin' error
"""
CORS(app)

# set default function for jsonify
def set_default(obj):
    if isinstance(obj, set):
        return list(obj)
    raise TypeError


# lamda takes data returns json response
def response(data): return app.response_class(
    response=json.dumps(data, default=set_default),
    status=200,
    mimetype='application/json'
)

# type handler for jsonify 
def type_handler(x):
    if isinstance(x, datetime.datetime):
        return x.isoformat()
    if isinstance(x, decimal.Decimal):
        return '$%.2f' % (x)
    raise TypeError("Unknown type")

# jsonify function with custom type handler
# convert datetime to isoformat and decimal to string
def rows_to_json(cols, rows):
    result = []
    for row in rows:
        data = dict(zip(cols, row))
        result.append(data)
    return json.dumps(result, default=type_handler)


@app.route('/')
def hello():
    # test api
    return 'Welcome Api setup sucessful'


@app.route('/test')
def test_get():
    try:
        # create mysql connection
        conn = pymysql.connect(host=config._DB_CONF['host'],
                               port=config._DB_CONF['port'],
                               user=config._DB_CONF['user'],
                               passwd=config._DB_CONF['passwd'],
                               db=config._DB_CONF['db'])
        cur = conn.cursor()
        # caluclating the time from now
        start_time = time.time()

        sql = "SELECT * FROM aisles LIMIT 3;"
        cur.execute(sql)

        # get all column names
        columns = [desc[0] for desc in cur.description]
        # get all data
        rows = cur.fetchall()

        # build json
        result = rows_to_json(columns, rows)
        # print(result)

        # end time
        compute_time = time.time() - start_time
        cur.close()
        conn.close()
        
        

        # response data
        response_data = {
            'data': result,
            'columns': columns,
            'compute_time': compute_time
        }
        return response(response_data)
    except Exception as e:
        return {'error': str(e)}


@app.route('/runsqlquery', methods=['POST'])
def run_mysql_query():
    # read post request data
    request_data = request.get_json()
    sql = request_data['sql']
    # print(sql)
    try:
        # create mysql connection
        conn = pymysql.connect(host=config._DB_CONF['host'],
                               port=config._DB_CONF['port'],
                               user=config._DB_CONF['user'],
                               passwd=config._DB_CONF['passwd'],
                               db=config._DB_CONF['db'])
        cur = conn.cursor()
        # caluclating the time from now
        start_time = time.time()

        cur.execute(sql)

        # get all column names
        columns = [desc[0] for desc in cur.description]
        # get all data
        rows = cur.fetchall()

        # build json
        result = rows_to_json(columns, rows)
        # print(result)

        # end time
        compute_time = time.time() - start_time
        cur.close()
        conn.close()

        # response data
        response_data = {
            'data': result,
            'compute_time': compute_time
        }
        return response(response_data)
    except Exception as e:
        return {'error': str(e)}

# todo wirte redshift query getter
@app.route('/runredshiftquery', methods=['POST'])
def run_redshift_query():
    request_data = request.get_json()
    sql = request_data['sql']
    try:
        # connect to redshift
        conn = psycopg2.connect(host=config._REDSHIFT_CONF['host'],
                                port=config._REDSHIFT_CONF['port'],
                                user=config._REDSHIFT_CONF['user'],
                                password=config._REDSHIFT_CONF['password'],
                                database=config._REDSHIFT_CONF['database'])
        cur = conn.cursor()
        # caluclating the time from now
        start_time = time.time()

        cur.execute(sql)

        # get all column names
        columns = [desc[0] for desc in cur.description]
        # get all data
        rows = cur.fetchall()

        # build json
        result = rows_to_json(columns, rows)
        # print(result)

        # end time
        compute_time = time.time() - start_time
        cur.close()
        conn.close()

        # response data
        response_data = {
            'data': result,
            'compute_time': compute_time
        }
        return response(response_data)
    except Exception as e:
        return {'error': str(e)}    


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500


if __name__ == '__main__':
    app.run(threaded=True, debug=True)

# [END app]
