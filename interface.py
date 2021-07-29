import logic
from loguru import logger
import warnings

warnings.filterwarnings('ignore')

logger.add("log.log", rotation="1 MB", enqueue=True, backtrace=True, diagnose=True)

try:
    print("Starting function.")
    logic.main()
except Exception:
    logger.Exception("Uncaught Exception Happened")

