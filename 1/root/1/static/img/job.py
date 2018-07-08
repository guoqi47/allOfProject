# coding:utf-8


from flask import Flask, request, session, jsonify, redirect, Response, send_file, render_template
from functools import wraps
import redis
import re
from datetime import timedelta
from send_sms import send_sms
import string
import time
from datetime import datetime
import random
import json
import pandas as pd
from job_db import *
from pymongo import MongoClient
import hashlib
import pandas
import os
import csv

app = Flask(__name__)

passwd_key = 'oknopk(8*lfdigjhDJGBEO%#&BGV'
app.secret_key = "sdfsdSDFSG566.dfopingrHmp58/OIP;"
app.permanent_session_lifetime = timedelta(days=30)
sess = session
redis_db = redis.StrictRedis(host='localhost', port=6379)
client = MongoClient("mongodb://localhost/", 27017)
data_db = client.number_db.data
column_db = client.number_db.columns
test_db = client.number_db.test
new_test_db = client.number_db.new_test
# 上传文件
UPLOAD_FOLDER = 'upload'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # 设置文件上传的目标文件夹
basedir = os.path.abspath(os.path.dirname(__file__))  # 获取当前项目的绝对路径

def check_session(f):
    @wraps(f)
    def decorated(*args, **kw):
        if "phone" in sess and "rank" in sess:
            return f(*args, **kw)
        else:
            url = "http://47.100.239.246:8080/login"
            return redirect(url)
    return decorated


@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == "POST":
        phone_num = request.form['phone']
        pass_word = request.form['pass_word']
        try:
            sms_code = int(request.form['sms_code'])
        except ValueError:
            sms_code = 0000
        user = db_session.query(User).filter(User.phone == phone_num, User.password == pass_word).first()
        if not user:
            # print("not user")
            return jsonify({})

        user_code = redis_db.get(phone_num)

        # 如表单内有验证码，且验证码与缓存内一致，则登录成功
        if sms_code != 0000 and sms_code == int(user_code) and user_code:
            sess['phone'] = user.phone
            sess['name'] = user.name
            sess['rank'] = user.rank
            loginfo = LoginInfo(user_id=user.id, time=datetime.now(), ip=request.remote_addr)
            db_session.add(loginfo)
            db_session.commit()
            return jsonify({'success': True, 'msg': 'OK', 'data': {'phone': user.phone, 'rank': user.rank}})
        elif sms_code != 0000 and user_code:
            return jsonify({'success': False, 'msg': '验证码错误'})
        # else:
        #     # 缓存内已有验证码，且当天发送次数未超过十次，两分钟内未发过，则重发短信
        #     if user_code:
        #         is_send = redis_db.get('today:%s' % phone_num)
        #         sms_limit = redis_db.get('last:%s' % phone_num)
        #         if is_send:
        #             return jsonify({'success': False, 'msg': '验证码已发送，请60秒后重试'})
        #         elif sms_limit > 10:
        #             return jsonify({'success': False, 'msg': '当日尝试次数超过10次'})
        #         send_sms(phone_num, '登录验证', "SMS_137365090", user_code)
        #         sms_limit.incr()
        #         return jsonify({'success': False, 'msg': '验证码已发送'})
        #     # 缓存内无验证码，发送并存入数据库
        #     else:
        #         code = ''.join(random.sample(string.digits, 6))
        #         send_sms(user.phone, '登录验证', "SMS_137365090", code)
        #         redis_db.set(phone_num, code, ex=300)
        #         redis_db.set('last:%s' % phone_num, 1, ex=86400)
        #         redis_db.set('today:%s' % phone_num, 1, ex=120)
        #         return jsonify({'success': False, 'msg': '验证码已发送'})

@app.route('/dataImport', methods=['POST','GET'])
def dataImport():
    if request.method == 'GET':
        return render_template('dataImport.html')
    elif request.method == "POST":
        file_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])  # 拼接成合法文件夹地址
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)  # 文件夹不存在就创建
        f = request.files['new_file']  # 从表单的file字段获取文件，myfile为该表单的name值
        if f:  # 判断是否是允许上传的文件类型
            fname = f.filename
            ext = fname.rsplit('.', 1)[1]  # 获取文件后缀
            unix_time = int(time.time())
            new_filename = str(unix_time) + '.' + ext  # 修改文件名
            f.save(os.path.join(file_dir, new_filename))  # 保存文件到upload目录
            # get data
            df = pd.read_csv(os.path.join(file_dir, new_filename))
            df.columns = ['phone', 'import_date','name',  'id_card_num', 'location',  'Is_true_name','package_name',
                          'net_age', 'city', 'virtual_net', 'family_net', 'estimate_guarantee', 'balance',
                          'domestic_data_flow', 'fly_package_domestic_voice', 'personalized_recommendation','business_recommendation',
                          'fourthGeneration_star_straight_down_target', 'three_months_avg_flow',
                          'three_months_avg_voice', 'three_months_avg_income', 'fourthGeneration_feiyue_time', 'fourthGeneration_feixiang_time',
                          'upto_feiyue', 'upto_feiyue_time', 'upto_feixiang', 'upto_feixiang_time', 'straight_down',
                          'straight_down_time', 'contract_plan_guarantee', 'contract_plan_guarantee_time', 'government_enterprise', 'government_enterprise_time',
                          'new_government_enterprise', 'new_government_enterprise_time', 'Telemarketing_activities_2017',
                          'Telemarketing_activities_2017_time', 'model']
            reader = df.to_dict(orient="records")
            for row in reader:
                new_test_db.insert(row)
            # csvfile.close()
            # 展示数据
            # cursor = new_test_db.find()
            # for document in cursor:
            #     print(document)
            # new_test_db.drop()
            return jsonify({"errno": 0, "errmsg": "上传成功"})
        else:
            return jsonify({"errno": 1001, "errmsg": "上传失败"})

@app.route('/get_sms', methods=['POST','GET'])
def get_sms():
    phone_num = request.form['phone']
    print("***#####", phone_num)
    pass_word = request.form['pass_word']
    print("***#####",pass_word)
    user = db_session.query(User).filter(User.phone == phone).first()
    # print("***",user.password)
    if not user:
        print('not user')
        # print()
        return jsonify({})
    user_code = redis_db.get(phone_num)
    if user_code:
        print(user_code)
        is_send = redis_db.get('today:%s' % phone_num)
        sms_limit = redis_db.get('last:%s' % phone_num)
        if is_send:
            print('is send')
            return jsonify({'success': False, 'msg': '验证码已发送，请60秒后重试'})
        # elif sms_limit > 10:
        #     return jsonify({'success': False, 'msg': '当日尝试次数超过10次'})
        send_sms(phone_num, '登录验证', "SMS_137365090", user_code)
        # sms_limit.incr()
        return jsonify({'success': False, 'msg': '验证码已发送'})
    # 缓存内无验证码，发送并存入数据库
    else:
        code = ''.join(random.sample(string.digits, 6))
        print('code:',code)
        send_sms(user.phone, '登录验证', "SMS_137365090", code)
        redis_db.set(phone_num, code, ex=300)
        redis_db.set('last:%s' % phone_num, 1, ex=86400)
        redis_db.set('today:%s' % phone_num, 1, ex=120)
        return jsonify({'success': False, 'msg': '验证码已发送'})


@app.route('/search', methods=['GET'])
# @check_session
def search():
    result_list = []
    args = dict(request.args)

    search_filter = {}
    for i in args:
        search_filter[i] = re.compile(args[i])

    result = data_db.find(search_filter)
    for i in list(result):
        result_list.append(i)
    column = column_db.find_one({})

    return jsonify({'success': True, 'msg': 'OK', 'data': {'result': result_list, 'column': column}})


@app.route('/bulk_search', methods=['POST'])
# @check_session
def bulk_search():
    num_list = request.form['num_list'].split('\r\n')
    result_list = []
    for i in num_list:
        result_list.append(data_db.find_one({'phone': i}))
    df = pandas.DataFrame(result_list)
    df.pop('_id')
    return Response(df.to_csv(index=False), mimetype="text/csv",
                    headers={"Content-disposition": u"attachment; filename=查询结果.csv".encode('utf-8')})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
