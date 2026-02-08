from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
import random

app = Flask(__name__)

data = {
    'temperature': 26.8,
    'temp_limits' : [],
    'mode' : 'auto',
    'heater_on' : False,
}




# phone-server

@app.route('/status', methods=['GET'])
def status():
    if request.method == 'GET':
        return "ok"
    return ""

@app.route('/get-temp', methods=['GET'])
def get_temp():
    if request.method == 'GET':
        req_type = request.args.get('type')
        print(req_type)

        return jsonify(data[req_type])
    return ""

@app.route('/set-temp-limits', methods=['POST'])
def set_temp_limits():
    if request.method == 'POST':
        answ = request.get_json()
        if answ['min_temp']:
            min_temp, max_temp = answ['min_temp'], answ['max_temp']
            data['temp_limits'] = [min_temp, max_temp]
            print(min_temp, max_temp)
    return ""

@app.route('/manual-mode', methods=['POST'])
def manual_mode():
    if request.method == 'POST':
        answ = request.get_json()
        if answ:
            try:
                turn_on_heater = answ['turn_on_heater']
                data['heater_on'] = turn_on_heater
                print(turn_on_heater)
            except Exception as e:
                print(e)
    return ""

@app.route('/set-mode', methods=['POST'])
def set_mode():
    if request.method == 'POST':
        answ = request.get_json()
        if answ:
            data['mode'] = answ['mode']

    return ""


# server-thermostat
@app.route('/send-temp', methods=['POST'])
def send_temp():
    if request.method == 'POST':
        answ = request.get_json()
        data['temperature'] = answ['temperature']
        print(data['temperature'])

    return  ""


@app.route('/get-control-mode', methods=['GET'])
def get_control_mode():
    if request.method == 'GET':
        data_ = {'mode' : data['mode']}
        if data_['mode'] == 'manual':
            data_['heater_on'] = data['heater_on']
        elif data_['mode'] == 'auto':
            data_['temp_limits'] = data['temp_limits']

        return jsonify(data_)
    return ""


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
