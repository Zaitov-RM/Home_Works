'''
 Создайте модуль. В нем создайте функцию, которая принимает список и
 возвращает из него случайный элемент. Если список пустой, функция
 должна вернуть None. Проверьте работу функций в этом же модуле
'''
from random import choice


spis=['1','2','3','4']
spis2=[]

def choicelist(lst):
      if lst:
            return choice(lst)
      else:
            return None


print(choicelist(spis))
print(choicelist(spis2))



