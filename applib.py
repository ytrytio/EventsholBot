from collections.abc import Any, Awaitable, Callable, Dict, List
from aiosqlite import connect, OperationalError, Row
from aiofiles import open as aiopen
from time import time as unixtime
from pathlib import Path


__all__ = [
    "logf", "with_db",
    "db_file", "log_file",
    "JsonDict"
]


db_file: Path = Path(__file__).parent/"server.sqlite"
log_file: Path = Path(__file__).parent/"log.txt"
JsonDict = Dict[str, Any]


async def logf(err: str | Exception, warn: int = 0):
    """Log.
    `txt` - error text.
    `warn` - warning level (0 - info, 1 - warning, >1 - error).
    """

    warn_level = 'E' if warn > 1 else 'W' if warn else 'I'
    async with open(log_file, 'a') as f:
        await f.write(f'[{warn_level}]-{unixtime()}:\n{err!s}\n\n')


async def with_db(default: Any) -> Callable[..., Awaitable[Any, Any, Any]]:
    async def decorator(func: Callable[..., Awaitable[Any, Any, Any]]) -> Callable[..., Awaitable[Any, Any, Any]]:
        async def wrapper(*args: List[Any], **kwargs: Dict[str, Any]) -> Callable[..., Awaitable[Any, Any, Any]]:
            async with connect(db_file, check_same_thread=False) as cursor:
                cursor.row_factory = Row
                try:
                    return func(cursor, *args, **kwargs)
                except Exception as e:
                    logf(f"Error in {func.__name__}({', '.join((f'{i!r}' for i in args))}): {str(e)}", 2)
                    return default
                except OperationalError as e:
                    logf(f"Error connecting to database: {str(e)}", 2)
                    raise e
        return await wrapper
    return decorator
