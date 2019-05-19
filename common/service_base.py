import atexit
import os

from common.utils import log_info, redis_ready, log_error
from lib.event_store import EventStore


class ServiceBase(object):

    def subscribe_to_domain_events(self):
        log_info('You need to over ride subscribe_to_domain_events.')
        pass


    def unsubscribe_from_domain_events(self):
        log_info('You need to over ride unsubscribe_from_domain_events.')
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

    def chk_redis_store_bad(self, chk_class, store):
        res = redis_ready(store.redis, [chk_class.name], 1, 'chk_redis_store_bad')
        chk_class.store_down = not res
        #log_info('!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! NOT READY  nt   %s   sd  %s   cnt: %s    %s' % (chk_class.not_ready, chk_class.store_down, chk_class.cnt, res))
        if chk_class.not_ready or chk_class.store_down:
            if chk_class.store_down:
                chk_class.not_ready_cnt += 1
                if chk_class.not_ready_cnt > chk_class.max_not_ready_cnt:
                    store = EventStore(chk_class.name)
                    self.init_store(chk_class, store)
                    return True
        return False

    def redis_chk(self, chk_class, store):
        try:
            if chk_class.mutex is True:
                return
            chk_class.mutex = True
            chk_class.cnt += 1
            chk_class.redis_down = not redis_ready(store.redis, [chk_class.name], 1, 'redis_chk service_base')
            if chk_class.store_down:
                chk_class.mutex = False
                chk_class.redis_cnt += 1
                #chk_class.redis_down = True
                #chk_class.not_ready = True
                #log_info('SUBBBBBBBBBBBBBBBBBBBBBBBBB22222222222 %s  redis_down %s ' % (chk_class.redis_cnt, chk_class.cnt))
                return
            #log_info('redis_chk %s  down ? %s  not_ready ? %s  %s  ' % (
            #    chk_class.redis_cnt, chk_class.redis_down, chk_class.not_ready, chk_class.cnt))
            if chk_class.redis_down:
                chk_class.redis_cnt += 1
                #chk_class.not_ready = True
            else:
                chk_class.not_ready = False
                #log_info('SUBBBBBBBBBBBBBBBBBBBBBBBBB33333333333 %s    %s' % (chk_class.redis_cnt, chk_class.cnt))
                chk_class.redis_cnt = 0

            chk_class.mutex = False
        except Exception as e:
            chk_class.redis_cnt += 1
            #chk_class.redis_down = True
            #chk_class.not_ready = True
            log_error(e)
            log_error('REDIS_CHK !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        finally:
            chk_class.mutex = False
            if chk_class.redis_cnt > chk_class.max_not_ready_cnt:
                chk_class.redis_down = True
                chk_class.not_ready = True