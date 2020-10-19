import atexit  # @UnresolvedImport

from apscheduler.scheduler import Scheduler


def init_scheduler():
    scheduler = Scheduler()
    atexit.register(lambda: scheduler.shutdown(wait=False))
    return scheduler
