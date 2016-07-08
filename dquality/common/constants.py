QUALITYCHECK_MEAN = 1
QUALITYCHECK_STD = 2
QUALITYCHECK_SAT = 3
STAT_START = 100
STAT_MEAN = 100

QUALITYERROR_LOW = -1
QUALITYERROR_HIGH = -2
NO_ERROR = 0

FILE_TYPE_HDF = 1
FILE_TYPE_GE = 2

mapper = {
    'QUALITYCHECK_MEAN' : 1,
    'QUALITYCHECK_STD' : 2,
    'QUALITYCHECK_SAT' : 3,
    'STAT_START' : 100,
    'STAT_MEAN' : 100,

    'QUALITYERROR_LOW' : -1,
    'QUALITYERROR_HIGH' : -2,
    'NO_ERROR' : 0,

    'FILE_TYPE_HDF' : 1,
    'FILE_TYPE_GE' : 2
}

def globals(name):
    return mapper[name]
