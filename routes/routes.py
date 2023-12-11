from flask import Blueprint, request, jsonify

from config.db import collection_name, collection_name1, collection_name2

router = Blueprint('router', __name__)
import requests
import json
import pandas as pd


# GET request
@router.route('/getPredData', methods=['GET'])
def get_todos():
    try:
        # Access parameters from the query string
        todo_id = request.args.get('id')
        date = request.args.get('date')

        # Concatenate todo_id and date to create a new identifier
        id = todo_id + "_" + date
        query = {'_id': id}

        # Check if actual data exists
        todos_act = list(collection_name1.find(query, {'_id': 0, 'data': 1}))
        if not todos_act:
            # Actual data not found, create an array of zeros for each hour
            actual_data = {"data_act": [{"act_kwh": 0.0} for _ in range(24)]}
        else:
            # Actual data found, extract values from the data
            formatted_data_act = {"data_act": []}
            for key, value in todos_act[0]["data"].items():
                formatted_data_act["data_act"].append({"act_kwh": value["act_kwh"]})
            actual_data = formatted_data_act

        # Check if predicted data exists
        todos_pred = list(collection_name.find(query, {'_id': 0, 'data': 1}))
        if not todos_pred:
            # Predicted data not found, create an array of zeros for each hour
            predicted_data = {"data_pred": [{"pre_kwh": 0.0} for _ in range(24)]}
        else:
            # Predicted data found, extract values from the data
            formatted_data_pred = {"data_pred": []}
            for key, value in todos_pred[0]["data"].items():
                formatted_data_pred["data_pred"].append({"pre_kwh": value["pre_kwh"]})

            predicted_data = formatted_data_pred

        # Combine actual and predicted data into a single dictionary
        response_data = {"actual_data": actual_data["data_act"], "predicted_data": predicted_data["data_pred"]}

        return {"data": response_data}

    except Exception as e:
        return {"error": str(e)}


@router.route('/get_sensorList', methods=['GET'])
def get_sensorList():
    try:
        lst = ['5f718b613291c7.03696209', '5f718c439c7a78.65267835', '614366bce31a86.78825897',
               '6148740eea9db0.29702291', '62307a944c9117.27764752', '625fb44c5fb514.98107900',
               '625fb9e020ff31.33961816', '6260fd4351f892.69790282', '627cd4815f2381.31981050',
               '629087dedbd477.79790710', '629094ee5fdff4.43505210', '6295bdace55341.17149388',
               '6295eb61511b31.65607460', '62a9920f75c931.62399458', '62a9d0d7af97e3.16097779',
               '62aad7f5c65185.80723547', '62b15dfee341d1.73837476', '62b595eabd9df4.71374208',
               '6349368c306542.16235883', '634e7c43038801.39310596', '6399a18b1488b8.07706749',
               '63a413c88f4716.77874329', '63a4195534d625.00718490', '63a4272631f153.67811394',
               '63aa9161b9e7e1.16208626', '63aaca5d76b0e8.04988241', '63ca403ccd66f3.47133508',
               '641c17bc672215.97177522']

        # Convert the cursor to a list
        todos_cursor = collection_name2.find({'id': {'$in' : lst}}, {'_id': 0, 'id': 1, 'name': 1})
        todos = [{'id': doc['id'], 'name': doc['name']} for doc in todos_cursor]

        # Return the data as JSON
        return jsonify({'sensorList': todos})
    except Exception as e:
        print(e)
        return jsonify({"error": "An error occurred"}), 500

@router.route('/getPredDataV2', methods=['GET'])
def getPredDataV2():
    try:
        # Access parameters from the query string
        todo_id = request.args.get('id') 
        date = request.args.get('date')
        # print(todo_id)
        # return

        # Concatenate todo_id and date to create a new identifier
        id = todo_id + "_" + date
        query = {'_id': id}

        # Check if actual data exists
        # todos_act = list(collection_name1.find(query, {'_id': 0, 'data': 1}))
        l1=[]
        todos_act=requests.get("https://multipoint.myxenius.com/Sensor_newHelper/getDataApi?sql=select%20raw_data,sensor_id,read_time%20from%20dlms_load_profile%20where%20sensor_id=%27{}%27%20and%20date%28read_time%29=%27{}%27&type=query".format(todo_id,date))
        data=json.loads(todos_act.text)
        l1.append(data['resource'])
        # print(len(l1))
        columns = ['sensor', 'Clock', 'R_Voltage', 'Y_Voltage', 'B_Voltage', 'R_Current', 'Y_Current',
            'B_Current', 'A', 'BlockEnergy-WhExp', 'B', 'C', 'D', 'BlockEnergy-VAhExp',
            'Kwh', 'BlockEnergy-VArhQ1', 'BlockEnergy-VArhQ4', 'BlockEnergy-VAhImp']
        
        datalist = [(entry['sensor_id'], entry['raw_data']) for i in range(len(l1)) for entry in l1[i]]
        
        df = pd.DataFrame([row[0].split(',') + row[1].split(',') for row in datalist], columns=columns)
        
        df = df.drop([
            'R_Voltage', 'Y_Voltage', 'B_Voltage', 'R_Current', 'Y_Current',
            'B_Current', 'A', 'BlockEnergy-WhExp', 'B', 'C', 'D', 'BlockEnergy-VAhExp',
            'BlockEnergy-VArhQ1', 'BlockEnergy-VArhQ4', 'BlockEnergy-VAhImp'], axis=1)
        pd.set_option('display.max_columns', None)
        df['Clock'] = pd.to_datetime(df['Clock'])
        df['Kwh'] = df['Kwh'].astype(float)
        df['Kwh'] = (df['Kwh']/1000)
        
        
        df['Clock'] = pd.to_datetime(df['Clock'])
        df.set_index(["Clock"],inplace=True,drop=True)
        
        df1 = df[['Kwh']].resample(rule="1H").sum()
        df1=df1.round(2)
        # return print(df1['Kwh'])    
        if not todos_act:
            # Actual data not found, create an array of zeros for each hour
            actual_data = {"data_act": [{"act_kwh": 0.0} for _ in range(24)]}
        else:
            # Actual data found, extract values from the data
            formatted_data_act = {"data_act": []}
            for value in df1["Kwh"]:
                formatted_data_act["data_act"].append({"act_kwh": value})
            actual_data = formatted_data_act
            # print(actual_data)
        # Check if predicted data exists
        todos_pred = list(collection_name.find(query, {'_id': 0, 'data': 1}))
        if not todos_pred:
            # Predicted data not found, create an array of zeros for each hour
            predicted_data = {"data_pred": [{"pre_kwh": 0.0} for _ in range(24)]}
        else:
            # Predicted data found, extract values from the data
            formatted_data_pred = {"data_pred": []}
            for key, value in todos_pred[0]["data"].items():
                formatted_data_pred["data_pred"].append({"pre_kwh": value["pre_kwh"]})

            predicted_data = formatted_data_pred

        # Combine actual and predicted data into a single dictionary
        response_data = {"actual_data": actual_data["data_act"], "predicted_data": predicted_data["data_pred"]}

        return {"data": response_data}

    except Exception as e:
        return {"error": str(e)}
    