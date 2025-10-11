# -*- coding:utf-8 -*-
# AUTHOR: Sun

from json import dumps
from pathlib import Path
from threading import Thread

from bottle import route, run, static_file, request

from bridge import Bridge, Client

bridge = Bridge()
server_client: Client | None = bridge.A
pi_client: Client | None = bridge.B

@route('/')
def index():
    return static_file('index.html', root='./static')

@route('/favicon.ico')
def favicon():
    return static_file('favicon.ico', root='./static')

@route('/assets/<filename:path>')
def static(filename):
    return static_file(filename, root='./static')

@route('/command/send', method='POST')
def command_send():
    """
    @brief 发送指令
    @details 通过server_client发送指令
    """
    command = request.json.get('command')
    if server_client and command:
        server_client.put(command)
        return 'OK'
    return 'ERROR'

@route('/command/receive')
def command_receive():
    """
    @brief 接收所有信息
    @details 通过server_client接收所有信息，组成字符串数组返回
    """
    messages = []
    if server_client:
        while not server_client.receive_is_empty():
            msg = server_client.get()
            if msg is not None:
                messages.append(msg)
    return dumps(messages)

@route('/image/list')
def image_list():
    # 检查debug目录是否存在
    debug_dir = Path('./debug')
    if not debug_dir.exists():
        return dumps([])
    
    # 获取debug目录下所有文件
    files = [f for f in debug_dir.iterdir() if f.is_file()]
    
    # 筛选出符合格式的文件
    valid_files: dict[int, list[str]] = {}
    for file in files:
        parts = file.stem.split('_')
        number = int(parts[0])

        file_list = valid_files.get(number, [])
        file_list.append(file.name)
        valid_files[number] = file_list
    
    if not valid_files:
        return dumps([])
    
    # 找到最大的数字
    max_number = max(valid_files.keys())
    
    # 筛选出所有具有最大数字的文件
    result = valid_files[max_number]
    
    return dumps(result)

@route('/image/<filename>')
def get_image(filename):
    return static_file(filename, root='./debug')

def run_server(port: int = 8080):
    thread = Thread(target=run, kwargs={'host': '0.0.0.0', 'port': port, 'quiet': True})
    thread.start()


if __name__ == '__main__':
    run(host='0.0.0.0', port=8080)