from collections import OrderedDict
from threading import RLock
from time import monotonic

class Interactions:
    def __init__(self, ttl=600, capacity=1000, clock=monotonic):
        self.ttl,self.capacity,self.clock=ttl,capacity,clock
        self.items=OrderedDict(); self.lock=RLock()
    def expire(self):
        now=self.clock()
        for key in list(self.items):
            if self.items[key][0] <= now: del self.items[key]
    def put(self,key,value):
        with self.lock:
            self.expire();self.items[key]=(self.clock()+self.ttl,value,set())
            while len(self.items)>self.capacity:self.items.popitem(last=False)
    def claim(self,key,user_id,data):
        with self.lock:
            self.expire(); entry=self.items.get(key)
            if not entry: return None
            _,value,clicked=entry
            if user_id in clicked or data not in value['buttons']:return None
            role=value['roles'].get(data,'target')
            allowed=(user_id==value['owner'] if role=='owner' else user_id!=value['owner'] if role=='other' else user_id==value['target'])
            if not allowed:return None
            clicked.add(user_id);return value
