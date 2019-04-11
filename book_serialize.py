import json,pickle

"""
1. Создать модуль music_serialize.py. 
В этом модуле определить словарь для вашей любимой музыкальной группы, например:
my_favourite_group = {
‘name’: ‘Г.М.О.’,
‘tracks’: [‘Последний месяц осени’, ‘Шапито’],
‘Albums’: [{‘name’: ‘Делать панк-рок’,‘year’: 2016},
{‘name’: ‘Шапито’,‘year’: 2014}]}

С помощью модулей json и pickle сериализовать данный словарь в json и в байты, 
вывести результаты в терминал. 
Записать результаты в файлы group.json, group.pickle соответственно. В файле group.json 
указать кодировку utf-8.
"""

my_books={"name":"Чайка по имени Джонатан Ливингстон",
        "author":"Ричард Бах","year":"1970",
          "quotes":["Пойми, что́ ты больше всего на свете хотел бы делать, - и делай.",
          "Совершенство не знает предела."]}

with open("text.json","w",encoding="utf-8") as f:
    json.dump(my_books,f)
    print("Wrote_1")


with open("text.pickle","bw") as f:
    pickle.dump(my_books,f)
    print("Wrote_2")




