import logging
import logging.handlers
import os

# Папка где лежит настоящий файл
LOG_FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
# Пусть до серверного лога
SERVER_LOF_FILE_PATH = os.path.join(LOG_FOLDER_PATH, 'server.log')

# Создаем именованный логгер с именем server
server_logger = logging.getLogger('server')

# Создаем обработчик с ротацией файлом по дням
# сообщения будут выводиться в SERVER_LOF_FILE_PATH
server_handler = logging.handlers.TimedRotatingFileHandler(SERVER_LOF_FILE_PATH, when='d')
#server_handler.setLevel(logging.INFO)

# Определяем Форматтер сообщения
# Связываем обработчик с форматером
server_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(module)s - %(message)s"))

# Связываем логгер с обработчиком
server_logger.addHandler(server_handler)

# Устанавливаем уровень сообщений логгера
server_logger.setLevel(logging.INFO)
