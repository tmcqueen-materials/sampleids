from enum import IntEnum
from collections import namedtuple

class CONFIDENCE(IntEnum):
  HIGH = 3
  MEDIUM = 2
  LOW = 1
  NONE = 0

SampleID = namedtuple('SampleID', ['lab_id','tool_id','date','sample_id','provenance_id', 'split_id', 'parents', 'extra', 'raw', 'confidence', 'why'], defaults=['','','','',[],'',[],'','',CONFIDENCE.NONE, ''])
