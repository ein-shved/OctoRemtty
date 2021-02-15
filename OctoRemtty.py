import asyncio
import pty
import os
import queue
import argparse

class TtyDevice:
    def __init__(self, path='/dev/ttyEth0', writer = None, *args, **kwargs):
        self.master, self.slave = pty.openpty()
        self.__unlink()
        self.ptyfile = os.ttyname(self.slave)
        self.ptylink = path
        os.symlink(self.ptyfile, self.ptylink)
        self.queue = queue.SimpleQueue()
        self.setWriter(writer, *args, **kwargs)

    def __del__(self):
        self.__unlink()
        os.close(self.slave)
        os.close(self.master)

    def __unlink(self):
        try:
            os.unlink(self.ptylink)
        except:
            pass

    def reader(self):
        data = os.read(self.master, 1024)
        self.queue.put(data)
        self.processQueue()

    def processQueue(self):
        while callable(self.writer) and not self.queue.empty():
            self.writer(self.queue.get(), *self.writer_args, **self.writer_kwargs)

    def setWriter(self, writer = None, *args, **kwargs):
        self.writer = writer
        self.writer_args = args
        self.writer_kwargs = kwargs
        self.processQueue()

    def write(self, data):
        os.write(self.master, data)

    def watch(self, loop):
        loop.add_reader(self.master, self.reader)

class PrinterServerProtocol(asyncio.Protocol):
    def __init__(self, tty):
        asyncio.Protocol.__init__(self)
        self.tty = tty

    def connection_made(self, transport):
        self.transport = transport
        peername = self.transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.tty.setWriter(self.write)

    def connection_lost(self, exc):
        self.tty.setWriter()
        peername = self.transport.get_extra_info('peername')
        print('Disconnected {}'.format(peername))

    def data_received(self, data):
        self.tty.write(data)

    def write(self, data):
        self.transport.write(data)


async def main(host, port, ttyPath):
    loop = asyncio.get_running_loop()
    tty = TtyDevice(ttyPath)

    server = await loop.create_server(
        lambda: PrinterServerProtocol(tty), host, port)

    tty.watch(loop)

    async with server:
        await server.serve_forever()

parser = argparse.ArgumentParser()
parser.add_argument('-p', dest='port', action='store_true', default=8234)
parser.add_argument('-o', dest='host', action='store_true', default=None)
parser.add_argument('-t', dest='tty', action='store_true',
                    default='/dev/ttyEth0')
options = parser.parse_args()

asyncio.run(main(options.host, options.port, options.tty))
