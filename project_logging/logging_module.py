# This Python script configures a basic logging mechanism for the project. It sets up logging to write messages
# to a log file ('bigdatateam7.log') with a specific format and log level. The script provides two utility functions,
# 'log_success' and 'log_error,' to log success messages at the INFO level and error messages at the ERROR level, respectively.

import logging

# Configure the logging
logging.basicConfig(
    filename='bigdatateam7.log',  # Name of the log file
    level=logging.INFO,      # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    filemode='w'             # Overwrite the log file each run; use 'a' to append
)

# Creating logger objects for success and error
logger = logging.getLogger()

def log_success(message: str) -> None:
    """
    Logs a success message for project events at the INFO level.

    Args:
        message (str): The success message to be logged.
    """
    logger.info(message)  # Logging success messages at INFO level

def log_error(message: str) -> None:
    """
    Logs an error message for project events at the ERROR level.

    Args:
        message (str): The error message to be logged.
    """
    logger.error(message)  # Logging error messages at ERROR level