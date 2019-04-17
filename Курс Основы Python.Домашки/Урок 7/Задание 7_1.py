''' Решить с помощью генераторов списка.
1. Даны два списка фруктов.
Получить список фруктов, присутствующих в обоих исходных списках.
'''
fruits1=['orange','banana','apple','waterlemon']
fruits2=['apple','lemon','orange','plum']
fruits=[fruit for fruit in fruits1 if fruit in fruits2]
print(fruits)

