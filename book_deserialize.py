import json,pickle

"""2: Создать модуль music_deserialize.py. В этом модуле открыть файлы group.json и 
group.pickle, прочитать из них информацию. Получить объект — 
словарь из предыдущего задания.
"""

with open("text.json","r",encoding="utf-8") as f:
    mybooks=json.load(f)
    print(mybooks)
    print(type(mybooks))

with open("text.pickle","br") as f:
    Mybooks=pickle.load(f)
    print(Mybooks)
    print(type(Mybooks))