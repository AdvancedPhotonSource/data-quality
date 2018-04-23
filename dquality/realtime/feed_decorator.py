from dquality.realtime.feed import Feed
import dquality.realtime.adapter as adapter
from epics import caget

class FeedDecorator(Feed):
    def __init__(self, decor):
        Feed.__init__(self)
        try:
            self.acq_time_pv = decor['rate_sat']
        except:
            self.acq_time_pv = None
        try:
            self.file_name_pv = decor['file_name']
        except:
            self.file_name_pv = None


    def get_packed_data(self, data, data_type):
        if self.acq_time_pv is None and self.file_name_pv is None:
            return adapter.pack_data(data, data_type)
        else:
            if not self.acq_time_pv is None:
                acq_time = caget(self.acq_time_pv)
            else:
                acq_time = None
            if self.file_name_pv is None:
                file_name = None
            else:
                # full_name = caget(self.file_name_pv, as_sting=True)
                # rev_full_name = full_name[::-1]
                # ind = rev_full_name.find('/')
                # rev_name = rev_full_name[0:ind]
                # file_name = rev_name[::-1]

                file_name = 'file'+str(caget('BBF1:cam1:ArrayCounter_RBV'))
            return adapter.pack_data_with_decor(data, data_type, acq_time, file_name)


