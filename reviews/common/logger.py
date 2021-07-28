from reviews.common.config import config
from loguru import logger
logger.add(config.get('project_physical_root_path') + "tmp/log/file.log", level=config.get('logger_severity_level'), rotation="5 MB", backtrace=True, diagnose=True)
