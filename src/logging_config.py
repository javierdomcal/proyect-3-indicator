import logging
import logging.config
import time
import os

# Configuración de logging con tres niveles de verbose: 0 (Bajo), 1 (Medio), 2 (Alto)
def setup_logging(verbose_level=1, log_file_name="program_log.log"):
    # Definir los niveles de logging en función del nivel de verbose
    console_level = logging.ERROR  # Nivel más bajo, por defecto se imprime solo errores
    file_level = logging.DEBUG  # Nivel más alto, siempre se guarda todo en el archivo

    if verbose_level == 1:
        console_level = logging.INFO  # Nivel medio, imprime información relevante
    elif verbose_level == 2:
        console_level = logging.DEBUG  # Nivel más alto, imprime todos los detalles

    logging_config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s [%(levelname)s] %(name)s %(funcName)s: %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': console_level,
                'formatter': 'standard',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': file_level,
                'formatter': 'detailed',
                'filename': log_file_name,
                'mode': 'a',  # Añadir logs al archivo existente
            }
        },
        'loggers': {
            '': {  # root logger para tu código
                'handlers': ['console', 'file'],
                'level': 'DEBUG',
                'propagate': True
            },
            'paramiko': {  # Reducción de verbose para bibliotecas externas
                'handlers': ['file'],
                'level': 'ERROR',  # Solo se registrarán errores de `paramiko`
                'propagate': False
            },
            # Puedes añadir más bibliotecas externas si es necesario
        }
    }
    logging.config.dictConfig(logging_config)
    logging.info(f"Logging initialized. Verbose level: {verbose_level}")

# Decorador para medir tiempos de ejecución y capturar errores
def log_execution_time(func):
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

# Función para crear un archivo de log por flujo de cálculo
def create_log_for_calculation(calculation_name, log_directory="logs"):
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)
    
    log_file_name = os.path.join(log_directory, f"{calculation_name}.log")
    return log_file_name
