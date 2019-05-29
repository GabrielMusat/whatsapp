import socketio
from flask import Flask, request
from lib.WebWhatsapp_Wrapper.webwhatsapi import WhatsAPIDriver
from lib.logger import Logger
import eventlet
import eventlet.wsgi
import os
import time
eventlet.monkey_patch()

logger = Logger('whatsapp')

app = Flask(__name__)
sio = socketio.Server(async_mode='threading')
app.wsgi_app = socketio.Middleware(sio, app.wsgi_app)

clients = []

FILES = os.path.join(os.path.split(__file__)[0], 'files')
PROFILE_PATH = os.path.join(os.path.split(__file__)[0], 'chrome_session')

if not os.path.isdir(FILES): os.mkdir(FILES)
if not os.path.isdir(PROFILE_PATH): os.mkdir(PROFILE_PATH)


class Whatsapp:
    def __init__(self):
        self.chats = {'Andromeda': '34662934560-1530867316@g.us', 'Yisas': '34652543310@c.us'}
        self.last_responses = {'Andromeda': time.time(), 'Yisas': time.time()}
        logger.info('launching whatsapp...')
        self.driver = WhatsAPIDriver(client='chrome', profile=PROFILE_PATH, headless=False)
        self.driver.wait_for_login(timeout=45)
        logger.info('whatsapp launched succesfully')

    def msg(self, chat, msg):
        try:
            if self.driver.is_logged_in():
                self.driver.chat_send_message(self.chats[chat], msg)
            else:
                self.driver.driver.refresh()
                self.driver.wait_for_login(timeout=30)
                self.driver.chat_send_message(self.chats[chat], msg)
        except Exception as e:
            logger.error(f'error sending msg {msg} to chat {chat}: {e}')

    def file(self, chat, file_path, caption=''):
        try:
            if self.driver.is_logged_in():
                self.driver.send_media(file_path, self.chats[chat], caption)
            else:
                self.driver.driver.refresh()
                self.driver.wait_for_login(timeout=30)
                self.driver.send_media(file_path, self.chats[chat], caption)
        except Exception as e:
            logger.error(f'error sending file {file_path} to chat {chat}: {e}')

    def run(self):
        while True:
            for chat in self.chats:
                try:
                    msgs = [m for m in self.driver.get_all_messages_in_chat(self.driver.get_chat_from_id(self.chats[chat]), include_me=True)]
                    msg = msgs[-1] if len(msgs) > 0 else None
                    if msg is None: continue
                    timestamp = time.mktime(msg.timestamp.timetuple())
                    if timestamp <= self.last_responses[chat]: continue
                    try:
                        msg_content = msg.content
                    except Exception as e:
                        logger.warning(f'message has no content, must be a media file: {e}')
                        continue
                    sio.emit(chat, msg_content)
                    self.last_responses[chat] = time.time()
                except Exception as e:
                    logger.error(f'error in search of new messages of chat {chat}: {e}')
            eventlet.sleep(1)


whatsapp = Whatsapp()


@app.route('/file', methods=['POST'])
def handleSendFile():
    logger.info(f'file send requested')
    params = request.args.to_dict()
    assert 'chat' in params, Exception('chat not in params')
    file = request.files['file']
    logger.info(f'saving file {file.filename} to {FILES}')
    file_path = os.path.join(FILES, file.filename)
    logger.info(f'saved')
    file.save(file_path)
    whatsapp.file(params['chat'], file_path, params['caption'] if 'caption' in params else '')
    logger.info(f'file sent correctly')
    whatsapp.last_responses[params['chat']] = time.time()
    return 'ok'


@app.route('/msg', methods=['POST'])
def handleSendMsg():
    logger.info(f'message send requested')
    params = request.args.to_dict()
    assert 'chat' in params, Exception('chat not in params')
    assert 'msg' in params, Exception('msg not in params')
    whatsapp.msg(params['chat'], params['msg'])
    logger.info(f'message sent correctly')
    whatsapp.last_responses[params['chat']] = time.time()
    return 'ok'


@sio.on('connect')
def handleConnect(sid, data):
    global clients
    clients.append(sid)
    logger.info(f'new connection {sid}! {len(clients)} client{"s" if len(clients) > 1 else ""} connected')


@sio.on('disconnect')
def handleDisconnect(sid):
    global clients
    clients.remove(sid)
    logger.info(f'client {sid} disconnected :( {f"{len(clients)} clients still connected" if len(clients) > 0 else "there are no clients connected"}')


if __name__ == '__main__':
    eventlet.spawn(whatsapp.run)
    eventlet.wsgi.server(eventlet.listen(('', 4000)), app)
