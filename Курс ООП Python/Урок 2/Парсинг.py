from bs4 import BeautifulSoup as BS
import re

with open("index.html","r",encoding="utf-8") as f:
      text=f.read()

#ищем номер телефона
find=re.findall("(tel:).+>(.+)</a",text)
#print(find)


#количество учеников
with open("index2.html","r",encoding="utf-8") as f:
      text2=f.read()

#print(re.findall("Нас уже (\d+\s\d+\s\d+) человек",text2))

soup=BS(text2,"html.parser")
#print(soup.prettify())

print(soup.find_all(class_='total-users'))

