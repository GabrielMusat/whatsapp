import socketio
import asyncio
from aiohttp import web
from lib.WebWhatsapp_Wrapper.webwhatsapi import WhatsAPIDriver
from lib.logger import Logger
import os
import time

logger = Logger('whatsapp')

app = web.Application()
sio = socketio.AsyncServer(async_mode='aiohttp')
sio.attach(app)


clients = []

FILES = os.path.join(os.path.split(__file__)[0], 'files')
PROFILE_PATH = os.path.join(os.path.split(__file__)[0], 'chrome_session')

if not os.path.isdir(FILES): os.mkdir(FILES)
if not os.path.isdir(PROFILE_PATH): os.mkdir(PROFILE_PATH)

# 'Arantxa': '34662934560@c.us'
class Whatsapp:
    def __init__(self):
        self.chats = {'Andromeda': '34662934560-1530867316@g.us', 'Yisas': '34652543310@c.us', '0_0': '34649883062-1545836929@g.us'}
        self.last_responses = {'Andromeda': time.time(), 'Yisas': time.time(), '0_0': time.time()}
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

    async def run(self):
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
                    await sio.emit(chat, msg_content)
                    self.last_responses[chat] = time.time()
                except Exception as e:
                    logger.error(f'error in search of new messages of chat {chat}: {e}')
            await asyncio.sleep(1)


whatsapp = Whatsapp()


async def handleSendFile(request):
    logger.info(f'file send requested')
    params = request.rel_url.query
    assert 'chat' in params, Exception('chat not in params')

    reader = await request.multipart()
    file = await reader.next()
    if file.name != 'file':
        logger.warning(f'se ha pasado un archivo que no tiene el nombre {file.name} en vez de file')
        return web.Response(text=f'se ha detectado el campo {file.name}, solo se permite el campo "file"', status=400)

    file_path = os.path.join(FILES, file.filename)
    with open(file_path, 'wb') as f:
        while True:
            chunk = await file.read_chunk()
            if not chunk: break
            f.write(chunk)

    whatsapp.file(params['chat'], file_path, params['caption'] if 'caption' in params else '')
    logger.info(f'file sent correctly')
    whatsapp.last_responses[params['chat']] = time.time()
    return web.Response(text='ok')


async def handleSendMsg(request):
    logger.info(f'message send requested')
    params = request.rel_url.query
    assert 'chat' in params, Exception('chat not in params')
    assert 'msg' in params, Exception('msg not in params')
    whatsapp.msg(params['chat'], params['msg'])
    logger.info(f'message sent correctly')
    whatsapp.last_responses[params['chat']] = time.time()
    return web.Response(text='ok')


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


app.add_routes([
    web.post('/file', handleSendFile),
    web.post('/msg', handleSendMsg)
])

if __name__ == '__main__':
    sio.start_background_task(whatsapp.run)
    web.run_app(app, host='0.0.0.0', port=4000)
