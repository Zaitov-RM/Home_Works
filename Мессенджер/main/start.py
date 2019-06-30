# Служебный скрипт запуска/останова нескольких клиентских приложений

from subprocess import Popen, CREATE_NEW_CONSOLE
import time

# список запущенных процессов
p_list = []

while True:
    user = input("Стандартный запуск (s) / Запуск нескольких клиентов (n)/ Выйти (q)")

    if user==('s'):
        p_list.append(Popen('python Server_rw.py',
                            creationflags=CREATE_NEW_CONSOLE))
        print('Сервер запущен')
        time.sleep(1)
        client_name = 'User0'
        p_list.append(Popen(f'python -i Client_r.py localhost 8888 r {client_name}',
                                 creationflags=CREATE_NEW_CONSOLE))
        client_name = 'User1'
        p_list.append(Popen(f'python -i Client_w.py localhost 8888 w {client_name}',
                            creationflags=CREATE_NEW_CONSOLE))
        
    elif user == 'n':
        # запускаем сервер
        # Запускаем серверный скрипт и добавляем его в список процессов
        p_list.append(Popen('python Server.py',
                            creationflags=CREATE_NEW_CONSOLE))
        print('Сервер запущен')
        # ждем на всякий пожарный
        time.sleep(1)
        n=int(input("Введите количество клиентов "))
        # запускаем клиентов на чтение
        for i in range(n):
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
