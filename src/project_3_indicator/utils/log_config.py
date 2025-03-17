import logging
import logging.config
import time
import os


def setup_logging(verbose_level=1, log_file_name="program_log.log"):
    """Configure logging with different verbosity levels."""
    console_level = logging.ERROR
    file_level = logging.DEBUG

    if verbose_level == 1:
        console_level = logging.INFO
    elif verbose_level == 2:
        console_level = logging.DEBUG

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "detailed": {
                "format": "%(asctime)s [%(levelname)s] %(name)s %(funcName)s: %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": console_level,
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            },
            "file": {
                "class": "logging.FileHandler",
                "level": file_level,
                "formatter": "detailed",
                "filename": log_file_name,
                "mode": "a",
            },
        },
        "loggers": {
            "": {
                "handlers": ["console", "file"],
                "level": "DEBUG",
                "propagate": True,
            },
            "paramiko": {
                "handlers": ["file"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
    logging.config.dictConfig(logging_config)
    logging.info(f"Logging initialized. Verbose level: {verbose_level}")


def log_execution_time(func):
    """Decorator to measure and log function execution time."""
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed_time = time.time() - start_time
            logger.info(f"Execution time for {func.__name__}: {elapsed_time:.2f} seconds")
            return result
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {elapsed_time:.2f} seconds: {e}")
            raise e
    return wrapper


def create_log_for_calculation(calculation_name, log_directory="logs"):
    """Create a log file for a specific calculation."""
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    log_file_name = os.path.join(log_directory, f"{calculation_name}.log")
    return log_file_name


if __name__ == "__main__":
    # Test logging configuration
    try:
        # Test different verbose levels
        print("Testing logging configuration:")
        for level in [0, 1, 2]:
            log_file = f"test_log_level_{level}.log"
            print(f"\nTesting verbose level {level}:")
            setup_logging(verbose_level=level, log_file_name=log_file)
            logging.debug("Debug message")
            logging.info("Info message")
            logging.warning("Warning message")
            logging.error("Error message")
            
            # Clean up test log file
            if os.path.exists(log_file):
                os.remove(log_file)
                
        # Test execution time decorator
        print("\nTesting execution time decorator:")
        @log_execution_time
        def test_function():
            time.sleep(1)
            return "Test completed"
            
        result = test_function()
        print(f"Function result: {result}")
        
        # Test calculation log creation
        print("\nTesting calculation log creation:")
        test_calc_name = "test_calculation"
        log_file = create_log_for_calculation(test_calc_name)
        print(f"Created log file: {log_file}")
        
        # Clean up test files
        if os.path.exists("logs"):
            import shutil
            shutil.rmtree("logs")
            
    except Exception as e:
        print(f"Test failed: {e}")