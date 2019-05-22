import atexit
import os
from datetime import timedelta

from timeloop import Timeloop

from common.utils import redis_ready, ChkClass
from lib.event_store import EventStore


class ServiceBase:

    def __init__(self, chk_class: ChkClass, store: EventStore, logger, start_timer=True):
        # FLASK logger
        self.log = logger
        self.set_loglevel()
        self.store = store
        self.chk_class = chk_class
        self.init_store(self.chk_class, self.store)
        chk_class.start_timer = start_timer
        self.t1 = None
        if start_timer:
            self.tl = Timeloop()

            @self.tl.job(interval=timedelta(seconds=3))
            def rc():
                self.redis_store_chk()

            self.start_timer()

    def get_logger(self):
        return self.log

    def set_loglevel(self):
        self.log.setLevel(self.chk_class.service.LOGLEVEL)

    def start_timer(self):
        self.tl.start()

    def stop_timer(self):
        self.tl.stop()

    def subscribe_to_domain_events(self):
        self.log.debug('You need to over ride subscribe_to_domain_events.')
        pass

    def unsubscribe_from_domain_events(self):
        self.log.debug('You need to over ride unsubscribe_from_domain_events.')
        pass

    def init_store(self, chk_class, store):
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            store.activate_entity_cache(chk_class.name)
            atexit.register(store.deactivate_entity_cache, chk_class.name)
            self.subscribe_to_domain_events()
            atexit.register(self.unsubscribe_from_domain_events)
            chk_class.not_ready = False
            chk_class.cnt = 0
            chk_class.not_ready_cnt = 0

    def service_store_bad(self, res=None):
        try:
            if res is None:
                res = redis_ready(self.store.redis, [self.chk_class.name], 1, 'service_store_bad')
            if res < 10:
                self.chk_class.not_ready_cnt += 1
                if self.chk_class.not_ready_cnt > self.chk_class.max_not_ready_cnt:
                    store = EventStore(self.chk_class.name)
                    self.init_store(self.chk_class, store)
                    return True
            return False
        except Exception as e:
            self.log.error('!!!!!!!!!!!!!! service_store_bad %s' % str(e))
            self.chk_class.not_ready_cnt += 1

    def redis_store_chk(self):
        try:
            if self.chk_class.mutex is True:
                return
            self.chk_class.mutex = True
            res = redis_ready(self.store.redis, [self.chk_class.name], 1, 'redis_store_chk service_base')
            if res < 10:
                self.chk_class.redis_cnt += 1
            else:
                self.chk_class.redis_cnt = 0

            self.chk_class.mutex = False
        except Exception as e:
            self.chk_class.redis_cnt += 1
            self.log.error('redis_store_chk exception: %s' % e)
        finally:
            self.chk_class.mutex = False
            if self.chk_class.redis_cnt > self.chk_class.max_not_ready_cnt:
                self.log.error('redis_store_chk ERROR: RESTARTING STORE  CNT: %s' % self.chk_class.redis_cnt)
                self.store = EventStore(self.chk_class.name)
                self.init_store(self.chk_class, self.store)

    def service_error(self, service_ready=None):
        if self.chk_class.redis_cnt > 0:
            self.log.debug('REDIS ERROR %s' % self.chk_class.redis_cnt)
            return True
        if service_ready is not None and service_ready > 0:
            self.log.debug('SERVICE ERROR %s' % self.chk_class.not_ready_cnt)
            return True
        return False
