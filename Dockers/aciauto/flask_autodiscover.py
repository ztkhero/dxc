#!/usr/bin/env python
from threading import Lock
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from FlaskAutoDiscover import APICAPI
import time

async_mode = None

app = Flask(__name__)
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()


def dbprint(msg):
    socketio.emit('apic_result',
                  {'data': msg},
                  namespace='/test')


# flask 的socketio与pyqt5 的socket emit非常的相似

def class_thread(socketio, mac="00:50:56:99:49:C6"):
    name = 'tzhang'
    pwd = 'vOkls2'
    apicip1 = "10.33.158.133"
    apicip2 = "10.41.158.133"

    dxcapic = APICAPI(name, pwd, apicip1, mac, socketio)
    swname,onapic2 = dxcapic.run()  # 从CDP的名字来检查对联是不是DC2的，如果连接的是LEF就是DC2，需要从走流程

    if ("LEF" in str(swname)) or onapic2:
        dbprint("Transfering APCI2 . . . . .")
        time.sleep(2)
        dxcapic = APICAPI(name, pwd, apicip2, mac, socketio)
        dxcapic.run()
    socketio.emit('enable_btn', namespace='/test')  # 结束后，让按钮恢复


@app.route('/')  # 静态路由，给一个网页
def index():
    return render_template('index.html', async_mode=socketio.async_mode)


# connect必须有，'connect'为socket event，在emit里面写上socket event就会被这个socket接收到
@socketio.on('connect', namespace='/test')
def test_connect():
    emit('my_response',
         {'data': 'Connected', 'count': 0})  # emit 让js里面的my_response socket接收到，这里的count是为了不让js程序读取count出错


@socketio.on('class_socket', namespace='/test')
def class_socket(mac):  # 函数形参会收到js发送过来的数据
    global thread
    print(mac['data'])  # 这里收到数据后，自动就转为dict了，应该是在修饰器里面就转换了
    with thread_lock:
        if thread is None:
            threadclass = socketio.start_background_task(class_thread(socketio, mac['data']))


if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=8035)
