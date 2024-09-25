import logging

# Configure the logging
logging.basicConfig(
    filename='bigdatateam7_data_storage.log',  # Name of the log file
    level=logging.INFO,      # Set the logging level to INFO
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    filemode='w'             # Overwrite the log file each run; use 'a' to append
)

# Creating logger objects for success and error
logger = logging.getLogger()

def log_success(message):
    logger.info(message)  # Logging success messages at INFO level

def log_error(message):
    logger.error(message)  # Logging error messages at ERROR level