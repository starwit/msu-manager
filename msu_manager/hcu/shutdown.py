import time


class ShutdownError(Exception):
    pass


class ShutdownModel:

    def __init__(self, delay_s: int):
        self._delay = delay_s
        self._timer_expiry_ts = None
        self._inhibition_end_ts = None

    @property
    def static_delay(self) -> int:
        return self._delay

    @property
    def time_remaining(self) -> float:
        if not self.is_active:
            raise ShutdownError('Shutdown is not active, has start() been called?')
        
        # Only consider inhibition if it extends beyond the current shutdown time
        if self.is_inhibited and self._inhibition_end_ts > self._timer_expiry_ts:
            return max(0, self._inhibition_end_ts - time.time())
        
        return max(0, self._timer_expiry_ts - time.time())

    @property
    def is_active(self) -> bool:
        return self._timer_expiry_ts is not None
    
    @property
    def is_inhibited(self) -> bool:
        return self._inhibition_end_ts is not None and self._inhibition_end_ts > time.time()

    def start(self):
        if not self.is_active:
            self._timer_expiry_ts = time.time() + self._delay

    def stop(self):
        self._timer_expiry_ts = None

    def inhibit(self, inhibit_time_s: int):
        self._inhibition_end_ts = time.time() + inhibit_time_s

    def reset(self):
        self._timer_expiry_ts = None
        self._inhibition_end_ts = None
    