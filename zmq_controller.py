import zmq
import os
from os.path import expanduser
import dquality.realtime.real_time as real
import threading


class zmq_rec():
    """
    This class represents ZeroMQ connection.
    """
    def __init__(self, host=None, port=None):
        """
        Constructor

        This constructor creates zmq Context and socket for the zmq.PAIR.
        It initiate connect to the server given by host and port.

        Parameters
        ----------
        host : str
            server host name

        port : str
            serving port

        """
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PAIR)
        self.socket.connect("tcp://" + host +":%s" % port)
        self.ver = None

    def destroy(self):
        """
        Destroys Context. This also closes socket associated with the context.
        """
        self.context.destroy()


def receive(zmq_host, zmq_rcv_port):
    """
    This function receives data from socket and enqueues it into a queue until the end is detected.

    Parameters
    ----------
    dataq : Queue
        a queue passing data received from ZeroMQ server to another process

    zmq_host : str
        ZeroMQ server host name

    zmq_rcv_port : str
        ZeroMQ port

    Returns
    -------
    none
    """

    conn = zmq_rec(zmq_host, zmq_rcv_port)
    socket = conn.socket
    interrupted = False
    while not interrupted:
        print ('waiting')
        msg = socket.recv_json()
        print 'got msg', msg
        key = msg.get("key")
        if key == "start_ver":
            print ('starting ver')
            detector = msg["detector"]
            home = expanduser("~")
            conf = os.path.join(home, '.dquality', detector)
            if os.path.isdir(conf):
                config = os.path.join(conf, 'dqconfig.ini')
            if not os.path.isfile(config):
                print ('missing configuration file')
            else:
                conn.ver = real.RT()
                th = threading.Thread(target=conn.ver.verify, args=(config,))
                th.start()

        elif key == "stop_ver":
            print('stopping')
            conn.ver.finish()

        else:
            pass

    print("Connection ended")

if __name__ == "__main__":
    receive('localhost', 5511)

