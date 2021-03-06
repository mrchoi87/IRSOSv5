#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2018 JiNong, Inc.
# All right reserved.
#
# MBlock beteen drivers
#

import json
import random
import datetime
from enum import IntEnum

class MEnum(IntEnum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

class BlkType(MEnum):
    NONE = 0
    OBSERVATION = 100  # { time: '2018-10-24 14:34:42', 1 : 123, 2 :456 }
    REQUEST = 200      # { id : 1, cmd : 'on/off', param : {....}}
    RESPONSE = 300     # { res : 'ok/err' }
    STATUS = 400       # { time: '2018-10-24 14:34:42', 1 : 0, 2 : 1}
    NOTICE = 500       # { ..... }
    UNDEFINED = 600

    @staticmethod
    def isobservation(blktype):
        return BlkType.OBSERVATION <= blktype and blktype < BlkType.REQUEST

    @staticmethod
    def isrequest(blktype):
        return BlkType.REQUEST <= blktype and blktype < BlkType.RESPONSE

    @staticmethod
    def isresponse(blktype):
        return BlkType.RESPONSE <= blktype and blktype < BlkType.STATUS

    @staticmethod
    def isstatus(blktype):
        return BlkType.STATUS <= blktype and blktype < BlkType.NOTICE

    @staticmethod
    def isnotice(blktype):
        return BlkType.NOTICE <= blktype and blktype < BlkType.UNDEFINED

    @staticmethod
    def isnotrequest(blktype):
        return BlkType.isobservation(blktype) or (BlkType.RESPONSE <= blktype and blktype < BlkType.UNDEFINED)

    @staticmethod
    def isundefined(blktype):
        return BlkType.UNDEFINED <= blktype

class ResCode(MEnum):
    OK = 0
    FAIL = 1
    FAIL_NO_DEVICE = 101
    FAIL_NOT_PROPER_COMMAND = 102
    FAIL_WRONG_KEYWORD = 103
    FAIL_TO_WRITE = 104
    #

class StatCode(MEnum):
    READY = 0    # OK, NORMAL
    ERROR = 1     # ABNORMAL
    BUSY = 2
    ERROR_VOLTAGE = 3
    ERROR_CURRENT = 4
    ERROR_TEMPERATURE = 5

    NEEDTOCHANGE = 101
    NEEDTOCALIBRATION = 102

    WORKING = 201
    OPENNING = 301
    CLOSING = 302

    PREPARING = 401    # MIXING
    SUPPLYING = 402
    STOPPING = 403

class CmdCode(MEnum):
    OFF = 0                 # STOP
    RESET = 1               # REBOOT
#SET = 2                 # complex param (object) not defined

    ON = 201                # no param
    TIMED_ON = 202          # param : time (sec) 
    DIRECTIONAL_ON = 203    # param : time (sec), ratio(-100 to 100)

    OPEN = 301              # no param
    CLOSE = 302             # no param
    TIMED_OPEN = 303        # param : time (sec)
    TIMED_CLOSE = 304       # param : time (sec)
    POSITION = 305          # param : position (0 to 100)
    SET_TIME = 306          # param : opentime, closetime

    ONCE_WATERING = 401     # no param
    PARAMED_WATERING = 402  # param : on-sec, start-area, stop-area, EC, pH
    CHANGE_CONTROL = 403    # param : control

    DETECT_DEVICE = 1001    # no param or (saddr, eaddr)
    CANCEL_DETECT = 1002    # no param
    DAEMON_RESTART = 1003   # no param 


    @staticmethod
    def getparams(cmdcode):
        _params = {
            CmdCode.TIMED_ON : ["hold-time"],
            CmdCode.DIRECTIONAL_ON : ["time", "ratio"],
            CmdCode.TIMED_OPEN : ["time"],
            CmdCode.TIMED_CLOSE : ["time"],
            CmdCode.POSITION : ["position"],
            CmdCode.SET_TIME : ["opentime", "closetime"],
            CmdCode.PARAMED_WATERING : ["EC", "pH", "on-sec", "start-area", "stop-area"],
            CmdCode.CHANGE_CONTROL : ["control"]
        }

        if cmdcode in _params:
            return _params[cmdcode]
        else:
            return []

class NotiCode(MEnum):
    DETECT_NODE_STARTED = 101              # ?????? ????????? ?????????
    DETECT_NODE_DETECTED = 102             # ????????? ?????????
    DETECT_UNKNOWN_PROTOCOL_VER = 103      # ???????????? ????????? ?????? ??????
    DETECT_UNKNOWN_NODE = 104              # ?????? ????????? ?????? ??????
    DETECT_WRONG_DEVICE = 105              # ?????? ????????? ????????? ??????
    DETECT_NO_NODE = 106                   # ????????? ??????
    DETECT_CANCELED = 107                  # ????????? ?????????
    DETECT_FINISHED = 108                  # ????????? ?????????

    ACTUATOR_STATUS = 201                  # ?????? ??????

    RTU_CONNECTED = 301                    # RTU ??????
    RTU_FAILED_CONNECTION = 302            # RTU ?????? ??????

    TCP_CONNECTED = 401                    # TCP ??????
    TCP_FAILED_CONNECTION = 402            # TCP ?????? ??????

    NODE_CONNECTED = 501                   # ????????? ???????????? ????????? ??? ??????

class MBlock(object):
    def __init__(self, nid, blktype, content, exkey=None, extra=None):
        self._nid = nid
        if isinstance(blktype, BlkType):
            self._type = blktype
        else:
            self._type = BlkType(blktype)
        self._content = content
        self.setextra(exkey, extra)

    def setextra(self, exkey, extra):
        self._exkey = exkey
        self._extra = extra

    def setkeyvalue(self, key, value):
        self._content[key] = value

    def getnodeid(self):
        return self._nid

    def gettype(self):
        return self._type

    def getcontent(self):
        return self._content

    def getextrakey(self):
        return self._exkey

    def getextra(self, key):
        if self._exkey != key:
            return None
        return self._extra

    def get(self):
        return {'nid' : self._nid, 'type' : self._type.value,
                'content' : self._content, 'exkey' : self._exkey, 'extra' : self._extra}

    def stringify(self):
        return json.dumps(self.get())

    @staticmethod
    def load(string):
        try:
            obj = json.loads(string)
            mblock = MBlock(obj['nid'], obj['type'], obj['content'], obj['exkey'], obj['extra'])
            if obj['type'] == BlkType.OBSERVATION:
                mblock.__class__ = Observation
            if obj['type'] == BlkType.REQUEST:
                mblock.__class__ = Request 
            if obj['type'] == BlkType.RESPONSE:
                mblock.__class__ = Response
            if obj['type'] == BlkType.STATUS:
                mblock.__class__ = Status 
            if obj['type'] == BlkType.NOTICE:
                mblock.__class__ = Notice 
            return mblock
        except Exception as ex:
            print "Fail to load a message.", ex
            return None

# OBSERVATION = 100  # { time: '2018-10-24 14:34:42', 1 : [123, StatCode], 2 : [456, StatCode]}
class Observation(MBlock):
    def __init__(self, nid, stat=None, exkey=None, extra=None):
        super(Observation, self).__init__(nid, BlkType.OBSERVATION, {}, exkey, extra)
        self.settime(None)
        self._content[str(nid)] = (0, StatCode.READY.value if stat is None else stat)

    def settime(self, tm):
        if tm is None:
            self._content["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self._content["time"] = tm
        return True

    def setobservation(self, devid, obs, stat=None):
        if stat is None:
            self._content[str(devid)] = (obs, StatCode.READY.value)
        else:
            self._content[str(devid)] = (obs, stat.value)
        return True

    def gettime(self):
        return self._content["time"]

    def getobservation(self, devid):
        return self._content[str(devid)][0]

    def getstatus(self, devid):
        return self._content[str(devid)][1]

# REQUEST = 200      # { id : 1, cmd : CmdCode, param : {...}}
class Request(MBlock):
    def __init__(self, nid, exkey=None, extra=None):
        super(Request, self).__init__(nid, BlkType.REQUEST, {}, exkey, extra)

    def setcommand(self, devid, cmd, params, opid=None):
        if opid is None:
            opid = random.randrange(1, 16000)
        self._content = {"id" : devid, "cmd" : cmd, "param" : params, "opid": opid}

    def getdevid(self):
        return self._content["id"]

    def getcommand(self):
        return self._content["cmd"]

    def getparams(self):
        if self._content["param"]:
            return self._content["param"]
        else:
            return {}

    def getopid(self):
        return self._content["opid"]

#RESPONSE = 300     # { res : ResCode }
class Response(MBlock):
    def __init__(self, req):
        key = req.getextrakey()
        super(Response, self).__init__(req.getnodeid(), BlkType.RESPONSE, {}, key, req.getextra(key))
        self._content["res"] = ResCode.FAIL.value
        self._content["opid"] = req.getopid()
        self._content["id"] = req.getdevid()

    def setresult(self, ret, exkey=None, extra=None):
        self._content["res"] = ret.value
        self.setextra(exkey, extra)

    def getresult(self):
        return self._content["res"]

    def getopid(self):
        return self._content["opid"]

"""
#STATUS = 400       # { time: '2018-10-24 14:34:42', 1 : 0, 2 : 1} 
class Status(MBlock):
    def __init__(self, nid, stat, exkey=None, extra=None):
        super(Status, self).__init__(nid, BlkType.STATUS, {}, exkey, extra)
        self.settime(None)
        self.setstatus(nid, stat)

    def settime(self, tm):
        if tm is None:
            self._content["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self._content["time"] = tm
        return True

    def setstatus(self, devid, stat):
        self._content[str(devid)] = stat
        return True

    def gettime(self):
        return self._content["time"]

    def getstatus(self, devid):
        return self._content[str(devid)]

    def get(self):
        content = {}
        for k, v in self._content.iteritems():
            if isinstance(v, StatCode):
                content[k] = v.value
            else:
                content[k] = v
        return {'nid' : self._nid, 'type' : self._type.value,
                'content' : content, 'exkey' : self._exkey, 'extra' : self._extra}
"""

#NOTICE = 500       # { code:NotiCode.Code, time: '2018-10-24 14:34:42', 1 : {'pos':...}, 2 : {}} 
class Notice(MBlock):
    def __init__(self, nid, code, devid=None, content=None, exkey=None, extra=None):
        super(Notice, self).__init__(nid, BlkType.NOTICE, {}, exkey, extra)
        self.settime(None)
        self._content["code"] = code.value
        if devid is not None:
            self.setcontent(devid, content)

    def settime(self, tm):
        if tm is None:
            self._content["time"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        else:
            self._content["time"] = tm
        return True

    def setcontent(self, devid, content):
        self._content[str(devid)] = content
        return True

    def gettime(self):
        return self._content["time"]

    def getcontent(self):
        return self._content

    def getcode(self): 
        return self._content["code"]

    def get(self):
        return {'nid' : self._nid, 'type' : self._type.value,
                'content' : self._content, 'exkey' : self._exkey, 'extra' : self._extra}

if __name__ == "__main__":
    blk = MBlock(10, BlkType.OBSERVATION, {1: 30})
    print blk.getcontent()
    print BlkType.isobservation(blk.gettype())
    print BlkType.isrequest(blk.gettype())
    print blk.get()

    blk = Observation(10)
    blk.setobservation(1, 30)
    blk.setobservation(2, 40)
    print blk.getcontent()
    print BlkType.isobservation(blk.gettype())
    print BlkType.isrequest(blk.gettype())
    print blk.get()

    blk = Request(10)
    blk.setcommand(1, 'on', {})
    print blk.getdevid()
    print blk.getcommand()
    print blk.stringify()
