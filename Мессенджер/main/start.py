# Служебный скрипт запуска/останова нескольких клиентских приложений

from subprocess import Popen, CREATE_NEW_CONSOLE
import time

# список запущенных процессов
p_list = []

while True:
    user = input("Запустить сервер и клиентов (s) / Выйти (q)")

    if user == 's':
        # запускаем сервер
        # Запускаем серверный скрипт и добавляем его в список процессов
        p_list.append(Popen('python Server.py',
                            creationflags=CREATE_NEW_CONSOLE))
        print('Сервер запущен')
        # ждем на всякий пожарный
        time.sleep(1)
        # запускаем клиентов на чтение
        for i in range(2):
            # Запускаем клиентский скрипт и добавляем его в список процессов
            client_name = f'User{i}'
            p_list.append(Popen(f'python -i Client.py localhost 8888 r {client_name}',
                                 creationflags=CREATE_NEW_CONSOLE))
        print('Клиенты запущены')

    elif user == 'q':
        print('Открыто процессов {}'.format(len(p_list)))
        for p in p_list:
            print('Закрываю {}'.format(p))
            p.kill()
        p_list.clear()
        print('Выхожу')
        break