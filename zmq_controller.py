import numpy as np
import zmq
import time


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
            interrupted = True
            conn.destroy()
        elif key == "stop_ver":
            print('stopping')

        else:
            pass

    print("Connection ended")

if __name__ == "__main__":
    receive('localhost', 5577)

