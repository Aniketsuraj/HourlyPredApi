from flask import Blueprint, request, jsonify

from config.db import collection_name, collection_name1, collection_name2

router = Blueprint('router', __name__)
import requests
import json
import pandas as pd
from datetime import datetime, timedelta


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
        print(todos_pred)

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

        return {"rc": 0, "message": "Success", "data": response_data}

    except Exception as e:
        return {"error": str(e)}


@router.route('/get_sensorList', methods=['GET'])
def get_sensorList():
    try:
        sensor_ids = ['5f718b613291c7.03696209', '5f718c439c7a78.65267835', '614366bce31a86.78825897',
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
        url = "https://multipoint.myxenius.com/Sensor_newHelper/getDataApi"
        params = {

            'sql': "SELECT id AS uuid, name AS sensorName, CASE WHEN UOM IS NOT NULL THEN UOM ELSE 'UOM' END AS uom FROM sensor WHERE id IN ({}) ORDER BY name".format(
                ','.join(f"'{sid}'" for sid in sensor_ids)),

            'type': 'query'
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        print("data=", data)
        sensor_list = [{'uuid': item['uuid'], 'sensorName': item['sensorName'], "UOM": item['uom']} for item in
                       data['resource']]
        print("sensor_list=", sensor_list)
        return jsonify({"rc": 0, "message": "Success", 'sensorList': sensor_list})
    except Exception as e:
        print(e)
        return jsonify({"rc": -1, "message": "error"}), 500


@router.route('/getPredDataDaily', methods=['GET'])
def getPredDataDaily():
    try:
        # Access parameters from the query string
        todo_id = request.args.get('id')
        date = request.args.get('date')

        month_from_date = (datetime.strptime(date, '%Y-%m-%d')).month
        month_today = (datetime.now()).month

        # Concatenate todo_id and date to create a new identifier
        id = todo_id + "_" + date
        query = {'_id': id}

        # Check if actual data exists
        l1 = []
        url = "https://multipoint.myxenius.com/Sensor_newHelper/getDataApi"
        params = {
            'sql': "select raw_data, sensor_id, read_time from dlms_load_profile where sensor_id='{}' and date(read_time)='{}' order by read_time"
            .format(todo_id, date),
            'type': 'query'
        }
        todos_act = requests.get(url, params=params)
        todos_act.raise_for_status()
        data = todos_act.json()
        l1.append(data['resource'])

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
        df['Kwh'] = (df['Kwh'] / 1000)
        df.set_index(["Clock"], inplace=True, drop=True)
        df1 = (df[['Kwh']].resample(rule="1H").sum()).round(2)

        if not todos_act:
            # Actual data not found, create an array of zeros for each hour
            actual_data = {"data_act": [{"hour": hour, "act_kwh": 0.0} for hour in range(24)]}
        else:
            formatted_data_act = {"data_act": []}
            actal_hour_counter, actual_Kwh_sum = 0, 0
            for value in df1["Kwh"]:
                formatted_data_act["data_act"].append({"hour": actal_hour_counter, "act_kwh": value})
                actual_Kwh_sum += value
                actal_hour_counter += 1
            if (len(formatted_data_act['data_act'])) < 24:

                for i in range((len(formatted_data_act['data_act'])), 24):
                    formatted_data_act["data_act"].append({"hour": i, "act_kwh": 0.0})
            # max_demand=df1['Kwh'].max()
            # max_demand_time=df1.loc[df1['Kwh'].idxmax()]
            # max_kwh_hour = max_demand_time.name.hour
            actual_data = formatted_data_act
            max_value_dict = max(actual_data['data_act'], key=lambda x: x['act_kwh'])
            actual_max_hour = str(max_value_dict['hour']).zfill(2)
            actual_max_value = round(max_value_dict['act_kwh'], 2)
            # print(actual_data)
        # Check if predicted data exists
        todos_pred = list(collection_name.find(query, {'_id': 0, 'data': 1}))
        if not todos_pred:
            # Predicted data not found, create an array of zeros for each hour
            predicted_data = {"data_pred": [{"hour": hour, "pre_kwh": 0.0} for hour in range(24)]}

        else:
            # Predicted data found, extract values from the data
            formatted_data_pred = {"data_pred": []}
            pred_hour_counter, pred_daily_sum = 0, 0
            for key, value in todos_pred[0]["data"].items():
                formatted_data_pred["data_pred"].append(
                    {"hour": pred_hour_counter, "pre_kwh": round(value["pre_kwh"], 2)})
                pred_daily_sum += (value["pre_kwh"])
                pred_hour_counter += 1

            predicted_data = formatted_data_pred
            max_value_dict = max(predicted_data['data_pred'], key=lambda x: x['pre_kwh'])
            pred_max_hour = str(max_value_dict['hour']).zfill(2)
            pred_max_value = round(max_value_dict['pre_kwh'], 2)
        if (month_from_date) != (month_today):
            percent = round(abs(((actual_Kwh_sum - pred_daily_sum) / actual_Kwh_sum) * 100), 2)
        else:
            percent = 0.0

        # Combine actual and predicted data into a single dictionary
        response_data = {"actual_data": actual_data["data_act"], "predicted_data": predicted_data["data_pred"]}

        return {"rc": 0, "message": "Success", "actual_daily_sum": round(actual_Kwh_sum, 2),
                # "actual_max_demand":max_demand,"actual_max_kwh_hour":max_kwh_hour,
                "actual_max_hour": actual_max_hour, "actual_max_value": actual_max_value,
                "pred_max_hour": pred_max_hour, "pred_max_value": pred_max_value,
                "pred_daily_sum": round(pred_daily_sum, 2), "data": response_data,
                "percentage": percent}

    except Exception as e:
        return {"error": str(e)}


@router.route('/getPredDataMonthly', methods=['GET'])
def getPredDataMonthly():
    try:
        todo_id = request.args.get('id')
        date = request.args.get('date')
        month_today = (datetime.now()).month
        date_object = datetime.strptime(date, '%Y-%m')
        first_date = date_object.replace(day=1)
        day, month, year = first_date.day, first_date.month, first_date.year
        last_date = (first_date.replace(month=first_date.month % 12 + 1, day=1, ) - timedelta(days=1))
        last_date = last_date.replace(hour=23, minute=30, year=year)
        last_day = last_date.day

        query = {"sensor_id": todo_id, "month": str(month), "year": str(year)}

        l1 = []
        url = "https://multipoint.myxenius.com/Sensor_newHelper/getDataApi"
        params = {
            'sql': "select raw_data, sensor_id, read_time from dlms_load_profile where sensor_id='{}' and month(read_time)='{}' and year(read_time)='{}' order by read_time"
            .format(todo_id, month, year),
            'type': 'query'
        }
        todos_act = requests.get(url, params=params)
        todos_act.raise_for_status()
        data = todos_act.json()
        l1.append(data['resource'])

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
        df['Kwh'] = (df['Kwh'] / 1000)

        df['Clock'] = pd.to_datetime(df['Clock'])
        df.set_index(["Clock"], inplace=True, drop=True)

        df1 = (df[['Kwh']].resample(rule="1D").sum()).round(2)

        if not todos_act:
            # Actual data not found, create an array of zeros for each hour
            actual_data = {"data_act": [{f"act_kwh{_}": 0.0} for _ in range(last_day)]}
        else:
            # Actual data found, extract values from the data
            formatted_data_act = {"data_act": []}

            monthly_sum = 0
            for value in df1["Kwh"]:
                formatted_data_act["data_act"].append(
                    {"clock": f"{year}-{month}-{str(day).zfill(2)}", "act_kwh": value})
                monthly_sum += value
                day += 1

            if (len(formatted_data_act['data_act']) != last_day):
                for i in range((len(formatted_data_act['data_act'])), (last_day)):
                    formatted_data_act["data_act"].append(
                        {"clock": f"{year}-{month}-{str(day).zfill(2)}", "act_kwh": 0.0})
                    day += 1

            actual_data = formatted_data_act
            # print(actual_data)
            act_max_value_in_month = max(actual_data['data_act'], key=lambda x: x['act_kwh'])
            act_max_date = str(act_max_value_in_month['clock'])

            # Check if predicted data exists
        todos_pred = list(collection_name.find(query, {'_id': 1, 'data': 1}))
        if not todos_pred:
            # Predicted data not found, create an array of zeros for each hour
            predicted_data = {"data_pred": [{f"pre_kwh{_}": 0.0} for _ in range(1, (last_day + 1))]}
            pred_max_value_in_month['pre_kwh'] == 0.0
        else:
            # Predicted data found, extract values from the data
            pred_monthly_sum = 0
            formatted_data_pred = {"data_pred": []}
            for i in range(len(todos_pred)):
                b = todos_pred[i]['_id'].split("_")
                date2 = b[1]
                pred_daily_sum = 0
                for y in range(24):
                    a = todos_pred[i]['data'][f"{y}"]['pre_kwh']
                    pred_daily_sum += a
                formatted_data_pred["data_pred"].append({"clock": date2, "pre_kwh": round(pred_daily_sum, 2)})
                pred_monthly_sum += pred_daily_sum
            predicted_data = formatted_data_pred
            pred_max_value_in_month = max(predicted_data['data_pred'], key=lambda x: x['pre_kwh'])
            pred_max_date = str(pred_max_value_in_month['clock'])
        if (month) != (month_today):
            percent = round(abs(((monthly_sum - pred_monthly_sum) / monthly_sum) * 100), 2)
        else:
            percent = 0.0
        # Combine actual and predicted data into a single dictionary
        response_data = {"actual_data": actual_data["data_act"], "predicted_data": predicted_data["data_pred"]}

        return {"rc": 0, "message": "Success",
                "act_max_value_in_month": act_max_value_in_month['act_kwh'], "act_max_date": act_max_date,
                "pred_max_value_in_month": pred_max_value_in_month['pre_kwh'], "pred_max_date": pred_max_date,
                "act_monthly_sum": round(monthly_sum, 2), "pred_monthly_sum": round(pred_monthly_sum, 2),
                "percent": percent, "data": response_data}

    except Exception as e:
        return {"error": str(e)}