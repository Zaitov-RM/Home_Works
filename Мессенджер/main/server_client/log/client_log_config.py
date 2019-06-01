import logging
import logging.handlers
import os

# Папка где лежит настоящий файл
LOG_FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))
# путь до клиентского лога
USER_LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, 'user.log')

# # Создаем именованный логгер с именем client
user_logger = logging.getLogger('user')
# устанавливаем уровень логгера
user_logger.setLevel(logging.INFO)

# обработчик будет логгер, который пишет в файл
user_handler = logging.FileHandler(USER_LOG_FILE_PATH, encoding='utf-8')
# задаем уровень обработчика
user_handler.setLevel(logging.INFO)

# настраиваем форматтер вывода
# связываем с форматером
user_handler.setFormatter(logging.Formatter("%(asctime)s - %(module)s - %(levelname)s - %(message)s"))

# связываем с обработчиком
user_logger.addHandler(user_handler)
