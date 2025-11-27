"""
错误处理和重试机制
基于tenacity库实现智能重试
"""
import asyncio
import functools
from typing import Callable, Optional, Type, Union
import logging

# 延迟导入tenacity
_tenacity = None


def _get_tenacity():
    """延迟加载tenacity"""
    global _tenacity
    if _tenacity is None:
        try:
            import tenacity
            _tenacity = tenacity
        except ImportError:
            pass
    return _tenacity


# 设置日志
logger = logging.getLogger(__name__)


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        exponential_base: float = 2.0,
        retry_exceptions: tuple = (Exception,),
    ):
        """
        初始化重试配置

        Args:
            max_attempts: 最大重试次数
            initial_delay: 初始延迟（秒）
            max_delay: 最大延迟（秒）
            exponential_base: 指数退避基数
            retry_exceptions: 需要重试的异常类型
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retry_exceptions = retry_exceptions


# 默认配置
DEFAULT_RETRY_CONFIG = RetryConfig()


def with_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None,
):
    """
    重试装饰器（同步函数）

    Args:
        config: 重试配置
        on_retry: 重试时的回调函数

    Usage:
        @with_retry()
        def my_function():
            # 可能失败的操作
            pass

        @with_retry(RetryConfig(max_attempts=5))
        def another_function():
            pass
    """
    cfg = config or DEFAULT_RETRY_CONFIG
    tenacity = _get_tenacity()

    def decorator(func: Callable) -> Callable:
        if tenacity:
            # 使用tenacity实现
            @tenacity.retry(
                stop=tenacity.stop_after_attempt(cfg.max_attempts),
                wait=tenacity.wait_exponential(
                    multiplier=cfg.initial_delay,
                    max=cfg.max_delay,
                    exp_base=cfg.exponential_base,
                ),
                retry=tenacity.retry_if_exception_type(cfg.retry_exceptions),
                before_sleep=_make_before_sleep_callback(on_retry) if on_retry else None,
                reraise=True,
            )
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper
        else:
            # 简单的回退实现
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                delay = cfg.initial_delay

                for attempt in range(cfg.max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except cfg.retry_exceptions as e:
                        last_exception = e
                        if attempt < cfg.max_attempts - 1:
                            if on_retry:
                                on_retry(attempt + 1, e)
                            logger.warning(
                                f"重试 {func.__name__} (尝试 {attempt + 1}/{cfg.max_attempts}): {e}"
                            )
                            import time
                            time.sleep(min(delay, cfg.max_delay))
                            delay *= cfg.exponential_base

                raise last_exception

            return wrapper

    return decorator


def with_async_retry(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable] = None,
):
    """
    异步重试装饰器

    Args:
        config: 重试配置
        on_retry: 重试时的回调函数

    Usage:
        @with_async_retry()
        async def my_async_function():
            # 可能失败的异步操作
            pass
    """
    cfg = config or DEFAULT_RETRY_CONFIG
    tenacity = _get_tenacity()

    def decorator(func: Callable) -> Callable:
        if tenacity:
            # 使用tenacity实现
            @tenacity.retry(
                stop=tenacity.stop_after_attempt(cfg.max_attempts),
                wait=tenacity.wait_exponential(
                    multiplier=cfg.initial_delay,
                    max=cfg.max_delay,
                    exp_base=cfg.exponential_base,
                ),
                retry=tenacity.retry_if_exception_type(cfg.retry_exceptions),
                before_sleep=_make_before_sleep_callback(on_retry) if on_retry else None,
                reraise=True,
            )
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper
        else:
            # 简单的回退实现
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                last_exception = None
                delay = cfg.initial_delay

                for attempt in range(cfg.max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except cfg.retry_exceptions as e:
                        last_exception = e
                        if attempt < cfg.max_attempts - 1:
                            if on_retry:
                                on_retry(attempt + 1, e)
                            logger.warning(
                                f"重试 {func.__name__} (尝试 {attempt + 1}/{cfg.max_attempts}): {e}"
                            )
                            await asyncio.sleep(min(delay, cfg.max_delay))
                            delay *= cfg.exponential_base

                raise last_exception

            return wrapper

    return decorator


def _make_before_sleep_callback(on_retry: Callable):
    """创建tenacity的before_sleep回调"""
    tenacity = _get_tenacity()
    if not tenacity:
        return None

    def callback(retry_state):
        attempt = retry_state.attempt_number
        exception = retry_state.outcome.exception()
        on_retry(attempt, exception)

    return callback


class CircuitBreaker:
    """断路器模式实现"""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_requests: int = 3,
    ):
        """
        初始化断路器

        Args:
            failure_threshold: 触发断路的失败次数
            recovery_timeout: 恢复超时时间（秒）
            half_open_requests: 半开状态允许的请求数
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_requests = half_open_requests

        self._failure_count = 0
        self._last_failure_time: Optional[float] = None
        self._state = "closed"  # closed, open, half_open
        self._half_open_successes = 0

    @property
    def state(self) -> str:
        """获取当前状态"""
        self._check_state_transition()
        return self._state

    def _check_state_transition(self):
        """检查状态转换"""
        import time

        if self._state == "open" and self._last_failure_time:
            elapsed = time.time() - self._last_failure_time
            if elapsed >= self.recovery_timeout:
                self._state = "half_open"
                self._half_open_successes = 0

    def record_success(self):
        """记录成功"""
        if self._state == "half_open":
            self._half_open_successes += 1
            if self._half_open_successes >= self.half_open_requests:
                self._state = "closed"
                self._failure_count = 0
        elif self._state == "closed":
            self._failure_count = max(0, self._failure_count - 1)

    def record_failure(self):
        """记录失败"""
        import time

        self._failure_count += 1
        self._last_failure_time = time.time()

        if self._state == "half_open":
            self._state = "open"
        elif self._failure_count >= self.failure_threshold:
            self._state = "open"

    def allow_request(self) -> bool:
        """是否允许请求"""
        self._check_state_transition()
        return self._state != "open"

    def __call__(self, func: Callable) -> Callable:
        """作为装饰器使用"""

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not self.allow_request():
                raise CircuitBreakerOpenError(
                    f"断路器打开，服务 {func.__name__} 暂时不可用"
                )

            try:
                result = func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise

        return wrapper

    def async_call(self, func: Callable) -> Callable:
        """异步装饰器"""

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            if not self.allow_request():
                raise CircuitBreakerOpenError(
                    f"断路器打开，服务 {func.__name__} 暂时不可用"
                )

            try:
                result = await func(*args, **kwargs)
                self.record_success()
                return result
            except Exception as e:
                self.record_failure()
                raise

        return wrapper


class CircuitBreakerOpenError(Exception):
    """断路器打开异常"""
    pass


class RAGError(Exception):
    """RAG模块基础异常"""
    pass


class IndexingError(RAGError):
    """索引相关错误"""
    pass


class RetrievalError(RAGError):
    """检索相关错误"""
    pass


class MemoryError(RAGError):
    """记忆相关错误"""
    pass


class ServiceMatchError(RAGError):
    """服务匹配错误"""
    pass


def safe_execute(
    default_value=None,
    exceptions: tuple = (Exception,),
    log_error: bool = True,
):
    """
    安全执行装饰器 - 捕获异常并返回默认值

    Args:
        default_value: 出错时返回的默认值
        exceptions: 要捕获的异常类型
        log_error: 是否记录错误日志

    Usage:
        @safe_execute(default_value=[])
        def get_items():
            # 可能失败的操作
            pass
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.error(f"{func.__name__} 执行失败: {e}")
                return default_value

        return wrapper

    return decorator


def safe_async_execute(
    default_value=None,
    exceptions: tuple = (Exception,),
    log_error: bool = True,
):
    """
    异步安全执行装饰器

    Args:
        default_value: 出错时返回的默认值
        exceptions: 要捕获的异常类型
        log_error: 是否记录错误日志
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                if log_error:
                    logger.error(f"{func.__name__} 执行失败: {e}")
                return default_value

        return wrapper

    return decorator
