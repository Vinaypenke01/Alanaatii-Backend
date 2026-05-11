import time
import logging

# Use the dedicated performance logger
logger = logging.getLogger('performance')

class RequestTimeMiddleware:
    """
    Middleware to log the duration of each request for performance monitoring.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Start timer
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log the performance data to the dedicated performance.log file
        log_msg = f"[PERF] {time.strftime('%Y-%m-%d %H:%M:%S')} | {request.method} {request.path} | Duration: {duration:.3f}s"
        
        # Log specifically to performance logger (logs/performance.log)
        logger.info(log_msg)
        
        return response
