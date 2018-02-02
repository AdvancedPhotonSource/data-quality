import zmq
import dquality.common.utilities as utils
import dquality.common.constants as const


class zmq_sen():
    def __init__(self, port=None):
        context = zmq.Context()
        self.socket = context.socket(zmq.PAIR)
        self.socket.bind("tcp://*:%s" % port)

def receive_send_zmq(dataq, zmq_rcv_port):
    conn = zmq_sen(zmq_rcv_port)
    socket = conn.socket
    interrupted = False
    while not interrupted:
        data = dataq.get()
        if data.status == const.DATA_STATUS_END:
            socket.send_json(
                dict(
                    key="end",
                    document="... see next message ...",
                ))
            interrupted = True
        else:
            slice = data.slice.flatten()
            print ('sending zmqdqu  ')
            socket.send_json(
                dict(
                    key="image",
                    dtype=str(slice.dtype),
                    shape=slice.shape,
                    # image_number=image_number,
                    # image_timestamp=image_time,
                    # sending_timestamp=time.time(),
                    # rotation=_cache_["rotation"],
                    # rotation_timestamp=rotation_time,
                    document="... see next message ...",

                ), zmq.SNDMORE
            )
            # binary image is not serializable in JSON, send separately
            socket.send(slice)

