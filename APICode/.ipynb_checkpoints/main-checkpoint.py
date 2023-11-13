#!/usr/bin/python
#coding:utf-8

from flask import Flask,jsonify,Response,request
import os
import logging
import pandas as pd
import pymysql
from sklearn.preprocessing import StandardScaler
from sklearn.externals import joblib
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop

app = Flask(__name__)

data_dir = os.path.join(os.getcwd(), 'data')
work_dir = os.path.join(os.getcwd(), 'model', os.path.basename(__file__).rstrip('.py'))

logger = logging.getLogger('Model')
logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.ERROR)

hostname = "127.0.0.1"
port = 3306
username = "root"
pwd = "password"
database = "dbname"

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class LostModel(metaclass=Singleton):
    def __init__(self):
        self.initVariable()

    def initVariable(self):
        self.conn = pymysql.connect(host=hostname, port=int(port), user=username, passwd=pwd,db=database, unix_socket="/tmp/mysql.sock",charset='utf8')
        self.clf = joblib.load('model/randomforestmodel.pkl')

    def detectIsLost(self,uid):
        if uid == None: return jsonify({'result': '-1'})
        if len(uid)<1: return jsonify({'result': '-2'})
        
        newdf = pd.read_sql("select ActivityCount,ActivityKeep,ActivityUsed,"
                            "IntegralCurrentPoints,IntegralUsed,IngegralTotal,"
                            "IntegralFrequency,IntegralAvgPointsDay,IntegralScanCount,"
                            "IntegralScanTotal,IntegralScanFrequency,IntegralCheckinCount,"
                            "IntegralCheckinFrequency,OrderCount,OrderFrequency,"
                            "OrderItemCount,OrderAvgPrice,OrderProvinceCity,"
                            "OrderAvgPoint,BabyCount,User_iCreator,ClientCode,"
                            "LoyaltyIsAutoLost from fwide_users where userid="+uid, con=self.conn)
        if newdf.shape[0] <=0 : return jsonify({'result': '-3'})

        newdf = newdf.fillna(0)
        factor = pd.factorize(newdf['OrderProvinceCity'])
        newdf.OrderProvinceCity = factor[0]

        X = newdf.iloc[:,0:len(newdf.columns.tolist())-1].values

        scaler = StandardScaler()
        x_input = scaler.fit_transform(X)
        print(x_input)
        y_pred = self.clf.predict(x_input)
        print(y_pred)
        return jsonify({'result': str(y_pred[0])})

@app.route('/api/v1.0/islost/<uid>', methods=['GET'])
def detectIsLost(uid):
    tager = LostModel()
    return tager.detectIsLost(uid)

if __name__ == '__main__':
    tager = LostModel()
    http_server = HTTPServer(WSGIContainer(app))
    http_server.listen(5000)
    IOLoop.instance().start()

