# coding:utf-8

from flask import Flask, request, session, jsonify, redirect, send_file, render_template, Response
from functools import wraps
import redis
from datetime import timedelta
from send_sms import send_sms
import string
import time
import random
import json
import pandas as pd
from job_db import *
from pymongo import MongoClient
import os
from datetime import datetime
import numpy as np

app = Flask(__name__)

passwd_key = 'oknopk(8*lfdigjhDJGBEO%#&BGV'
app.secret_key = "sdfsdSDFSG566.dfopingrHmp58/OIP;"
app.permanent_session_lifetime = timedelta(minutes=60)
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


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == "POST":
        phone_num = request.form['phone_num']
        pass_word = request.form['password']
        try:
            sms_code = int(request.form['sms_code'])
        except ValueError:
            sms_code = 0000
        user = db_session.query(User).filter(User.phone == phone_num, User.password == pass_word).first()
        if not user:
            return jsonify({})
        user_code = redis_db.get(phone_num)
        if not user_code:
            code = ''.join(random.sample(string.digits, 6))
            send_sms(user.phone, '登录验证', "SMS_137365090", code)
            redis_db.set(phone_num, code, ex=300)
            redis_db.set('last:%s' % phone_num, 1, ex=86400)
            redis_db.set('today:%s' % phone_num, 1, ex=120)
            user_code = code

        # 如表单内有验证码，且验证码与缓存内一致，则登录成功
        if sms_code != 0000 and sms_code == int(user_code):
            sess['phone'] = user.phone
            sess['name'] = user.name
            sess['rank'] = user.rank
            user.last_login = datetime.now()
            user.last_ip = request.remote_addr
            loginfo = LoginInfo(user_id=user.id, time=datetime.now(), ip=request.remote_addr)
            db_session.add(loginfo)
            db_session.commit()
            print('ssssssss')
            return redirect('/query')
        else:
            return jsonify({'success': False, 'msg': '验证码错误'})


def strip_han(co_str):
    try:
        return float(co_str)
    except ValueError:
        return float(co_str[:-1])


@app.route('/dataImport', methods=['POST', 'GET'])
# @check_session
def data_import():
    if request.method == 'GET':
        if sess['rank'] == 'admin':
            return render_template('dataImport.html')
        else:
            return "没有导入权限"
    elif request.method == "POST":
        if sess['rank'] != 'admin':
            return "没有导入权限"
        try:
            f = request.files['new_file']
            try:
                f_data = pd.read_excel(f)
            except:
                f_data = pd.read_excel(f)
            f_data.fillna("", inplace=True)

            f_data.rename(columns=change_columns, inplace=True)
            now = time.time()
            if "import_date" in f_data.columns:
                f_data['import_date'] = now
            if "id_card_num" in f_data.columns:
                f_data['id_card_num'] = f_data['id_card_num'].astype(np.str)
            if "phone" in f_data.columns:
                f_data['phone'] = f_data['phone'].astype(np.str)
                f_data['phone'] = f_data['phone'].map(lambda x: x.split('.')[0])
            if "balance" in f_data.columns:
                f_data["balance"] = f_data["balance"].map(strip_han)
            if "net_age" in f_data.columns:
                f_data['net_age'] = f_data['net_age'].map(strip_han)

            for i in ['fourG_feiyue_time', 'fourG_feixiang_time', 'upto_feiyue_time', 'upto_feixiang_time',
                      'straight_down_time', 'contract_guarantee_time', 'gov_enterprise_time',
                      'new_gov_enterprise_time', 'Tel_act_2017_time']:
                if i in f_data.columns:
                    f_data[i] = f_data[i].map(lambda x: int(time.mktime(time.strptime(x, "%Y-%m-%d %H:%M:%S"))) if x != "" else x)
            dictData = f_data.to_dict(orient="records")
            for row in dictData:
                phone = row.pop('phone')
                if phone != "":
                    new_test_db.update({"phone": phone}, {"$set": row}, True, True)
            return "导入成功"
        except Exception as e:
            print(e)
            return "上传失败，请检查上传文件格式"


@app.route('/get_sms', methods=['POST'])
def get_sms():
    phone_num = request.form['phone_num']
    pass_word = request.form['password']
    user = db_session.query(User).filter(User.phone == phone_num, User.password == pass_word).first()
    if not user:
        return jsonify({'success': False, 'msg': '用户名或密码不正确！'})
    user_code = redis_db.get(phone_num)
    if user_code:
        is_send = redis_db.get('today:%s' % phone_num)
        sms_limit = int(redis_db.get('last:%s' % phone_num))
        if is_send:
            return jsonify({'success': False, 'msg': '验证码已发送，请60秒后重试'})
        elif sms_limit > 11:
            return jsonify({'success': False, 'msg': '当日尝试次数超过30次'})
        send_sms(phone_num, '登录验证', "SMS_137365090", user_code)
        redis_db.set('last:%s' % phone_num, sms_limit + 1)
        return jsonify({'success': False, 'msg': '验证码已发送'})
    # 缓存内无验证码，发送并存入数据库
    else:
        code = ''.join(random.sample(string.digits, 6))
        print("验证码：",code)
        send_sms(user.phone, '登录验证', "SMS_137365090", code)
        redis_db.set(phone_num, code, ex=300)
        redis_db.set('last:%s' % phone_num, 1, ex=86400)
        redis_db.set('today:%s' % phone_num, 1, ex=60)
        return jsonify({'success': False, 'msg': '验证码已发送'})


@app.route('/search', methods=['GET'])
# @check_session
def search():
    search_filter = {}
    search_data = request.form['search']
    for i in search_data:
        if i['id'] == 'import_date':
            if len(i['CustomList']) == 0:
                continue
            if len(i['CustomList']) != 2:
                return '搜索数据错误'
            start_date = i['CustomList'][0]
            end_date = i['CustomList'][1]
            search_data['import_date'] = {}
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S').timestamp()
                search_data['import_date']['$gt'] = start
            except ValueError:
                pass
            try:
                end = datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S').timestamp()
                search_data['import_date']['$lt'] = end
            except ValueError:
                pass
        elif i['id'] == 'id_card_num':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'true_name':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'location':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'package_name':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'net_age':
            if len(i['CustomList']) != 1:
                return '搜索数据错误'
            if i['CustomList'][0][0] == ">":
                try:
                    num = int(i['CustomList'][0][1:])
                    search_data['net_age'] = {'$gt': num}
                except ValueError:
                    pass
            elif i['CustomList'][0][0] == "<":
                try:
                    num = int(i['CustomList'][0][1:])
                    search_data['net_age'] = {'$lt': num}
                except ValueError:
                    pass
            else:
                try:
                    num = int(i['CustomList'][0])
                    search_data['net_age'] = num
                except ValueError:
                    pass
        elif i['id'] == 'city':
            if len(i['CustomList']) != 0:
                search_data['city'] = {"$in": i['CustomList']}
        elif i['id'] == 'virtual_net':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'family_net':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'estimate_guarantee':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'balance':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'domestic_flow':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'fly_domestic_voice':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'personal_recommend':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'business_recommend':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'fourG_star_down_target':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'three_months_avg_flow':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'three_months_avg_voice':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'three_months_avg_income':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'fourG_feiyue_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'fourG_feixiang_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'upto_feiyue':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'upto_feiyue_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'upto_feixiang':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'upto_feixiang_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'straight_down':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'straight_down_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'contract_guarantee':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'contract_guarantee_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'gov_enterprise':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'gov_enterprise_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'new_gov_enterprise':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'new_gov_enterprise_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'Tel_act_2017':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'Tel_act_2017_time':
            if len(i['CustomList']) == 0:
                continue
        elif i['id'] == 'model':
            if len(i['CustomList']) == 0:
                continue
    result_list = []
    total = new_test_db.find(search_filter, {'phone': True, 'name': True, 'id_card_num': True, 'location': True,
                                              'package_name': True}).count()
    page = request.form['page']
    try:
        page = int(page)
    except ValueError:
        page = 0
    result = new_test_db.find(search_filter, {'phone': True, 'name': True, 'id_card_num': True, 'location': True,
                                              'package_name': True, "_id": False}).limit(50)
    for i in list(result):
        result_list.append(i)
    return jsonify({'success': True, 'msg': 'OK', 'data': {'result': result_list, 'total': total, 'page': page}})

@app.route('/filter', methods=['POST', 'GET'])
def filter():
    if request.method == 'GET':
        return render_template('filter.html')

@app.route('/query', methods=['GET'])
# @check_session
def query():
    return render_template('query.html')


@app.route('/management', methods=['GET'])
# @check_session
def management():
    # if sess['rank'] == 'admin':
    content = open('templates/management.html').read()
    return Response(content, mimetype="text/html")
    # else:
    #     return "没有权限"


@app.route('/bulk_search', methods=['POST'])
# @check_session
def bulk_search():
    column_index = ['phone', 'import_date', 'name', 'id_card_num', 'true_name', 'location', 'package_name',
                    'net_age', 'city', 'virtual_net', 'family_net', 'estimate_guarantee', 'balance',
                    'domestic_flow',
                    'fly_domestic_voice', 'personal_recommend', 'business_recommend', 'fourG_star_down_target',
                    'three_months_avg_flow', 'three_months_avg_voice', 'three_months_avg_income',
                    'fourG_feiyue_time',
                    'fourG_feixiang_time', 'upto_feiyue', 'upto_feiyue_time', 'upto_feixiang',
                    'upto_feixiang_time', 'straight_down',
                    'straight_down_time', 'contract_guarantee', 'contract_guarantee_time', 'gov_enterprise',
                    'gov_enterprise_time',
                    'new_gov_enterprise', 'new_gov_enterprise_time', 'Tel_act_2017', 'Tel_act_2017_time',
                    'model']
    num_list = request.form['num_list'].split('\r\n')
    result_list = []
    for i in num_list:
        x = new_test_db.find_one({'phone': i}, {"_id": False})
        if x:
            result_list.append(x)
    if not len(result_list):
        return "未查询到对应数据"
    df = pd.DataFrame(result_list)
    df = df[column_index]
    column = column_db.find_one({})
    names = {}
    for i in column:
        if i in df.columns:
            names[i] = column[i]

    df.rename(columns=names, inplace=True)
    writer = pd.ExcelWriter(app.root_path + '/output.xlsx')
    df.to_excel(writer, 'Sheet1', index=False)
    writer.save()

    return send_file(app.root_path + '/output.xlsx', as_attachment=True, attachment_filename='查询结果.xlsx')


def change_columns(cn_name):
    columns_map = {"电话": 'phone', "导入日期": 'import_date', "姓名": 'name', "身份证号码": 'id_card_num', "实名": 'true_name',
                   "地址": 'location', "套餐名称": 'package_name', "网龄": 'net_age', "县市": 'city', "虚拟网": 'virtual_net',
                   "亲情网": 'family_net', "保底预估费": 'estimate_guarantee', "余额": 'balance', "国内数据流量": 'domestic_flow',
                   "飞享套餐国内语音": 'fly_domestic_voice', "个性化推荐": 'personal_recommend', "业务推荐": 'business_recommend',
                   "4G明星机直降目标": 'fourG_star_down_target', "近三个月平均移动数据上网流量【月】": 'three_months_avg_flow',
                   "近三个月通话平均时长【月】": 'three_months_avg_voice', "出账-近三个月平均收入【月】": 'three_months_avg_income',
                   "4G飞悦套餐时间": 'fourG_feiyue_time', "4G飞享套餐时间": 'fourG_feixiang_time', "升飞悦": 'upto_feiyue',
                   "升飞悦时间": 'upto_feiyue_time', "升飞享": 'upto_feixiang', "升飞享时间": 'upto_feixiang_time',
                   "（直降）": 'straight_down', "（直降）时间": 'straight_down_time', "合约计划-保底": 'contract_guarantee',
                   "合约计划-保底时间": 'contract_guarantee_time', "政企": 'gov_enterprise', "政企时间": 'gov_enterprise_time',
                   "【新】政企合约": 'new_gov_enterprise', "【新】政企合约时间": 'new_gov_enterprise_time',
                   "2017话务营销活动": 'Tel_act_2017', "2017话务营销活动时间": 'Tel_act_2017_time', "机型": 'model'}
    if cn_name in columns_map:
        return columns_map[cn_name]
    else:
        return cn_name


@app.route('/logout', methods=['GET'])
@check_session
def logout():
    print("logout")
    sess.pop('phone')
    sess.pop('rank')
    redirect('/login')


@app.route('/user_manage', methods=['GET'])
@check_session
def user_manage():
    # if sess['rank'] != 'admin':
    #     return "没有权限"
    users = db_session.query(User).filter(User.rank != 'admin')
    user_list = []
    for i in users:
        last_login = i.last_login
        if last_login:
            last_time = last_login.time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            last_time = ''
        user_list.append({'name': i.name, 'phone': i.phone, 'id': i.id, 'last_ip': i.last_ip,
                          'last_login': last_time})
    return jsonify({"success": True, 'msg': 'OK', 'data': {'user_list': user_list}})


@app.route('/add_user', methods=['POST'])
# @check_session
def add_user():
    # if sess['rank'] != 'admin':
    #     return "没有权限"
    print("add~~~~~~~~~~~~~~~~~")

    user_phone = request.form['phone']
    pass_word = request.form['password']
    if pass_word == '':
        pass_word = 'c73bc206723045db4048bc3f0926987b'
    user_name = request.form['name']
    print("*******",user_phone,pass_word,user_name)
    new_user = User(name=user_name, phone=user_phone, password=pass_word, rank='user')
    db_session.add(new_user)
    db_session.commit()
    return jsonify({'success': True, 'msg': 'OK', 'data': {}})


@app.route('/del_user', methods=['POST'])
# @check_session
def del_user():
    # if sess['rank'] != 'admin':
    #     return "没有权限"
    user_id = request.form['user_id']
    print(user_id)
    try:
        user_id = int(user_id)
    except ValueError:
        return jsonify({'success': False, 'msg': 'Wrong user id', 'data': {}})
    user = db_session.query(User).filter(User.id == user_id).first()
    db_session.delete(user)
    db_session.commit()
    return jsonify({'success': False, 'msg': 'OK', 'data': {}})


@app.route('/forget_pass', methods=['POST'])
def forget_pass():
    phone_num = request.form['phone_num']
    pass_word = request.form['new_password']
    try:
        sms_code = int(request.form['sms_code'])
    except ValueError:
        sms_code = 0000
    user = db_session.query(User).filter(User.phone == phone_num, User.password == pass_word).first()
    if not user:
        return jsonify({})
    user_code = redis_db.get(phone_num)
    if not user_code:
        code = ''.join(random.sample(string.digits, 6))
        send_sms(user.phone, '登录验证', "SMS_137365090", code)
        redis_db.set(phone_num, code, ex=300)
        redis_db.set('last:%s' % phone_num, 1, ex=86400)
        redis_db.set('today:%s' % phone_num, 1, ex=120)
        user_code = code

    if sms_code != 0000 and sms_code == int(user_code):
        user.password = pass_word
        db_session.commit()
        return redirect('/query')
    else:
        return jsonify({'success': False, 'msg': '验证码错误'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
