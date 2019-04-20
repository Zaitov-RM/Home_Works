"""
1. Получите текст из файла.
2. Разбейте текст на предложения.
3. Найдите самую используемую форму слова, состоящую из 4 букв и более, на русском языке.
4. Отберите все ссылки.
5. Ссылки на страницы какого домена встречаются чаще всего?
6. Замените все ссылки на текст «Ссылка отобразится после регистрации».
"""
import re



#1)Получите текст из файла
with open("text.txt","r", encoding="utf-8") as f:
      text=f.read()

#2)Делим текст на предложения
sent=re.split("[!\.]\s",text)

#3)Самое распространенное слово в тексте
words=text.split(" ")
words=[x for x in words if len(x)>=4 and "." not in x]

lst=[]
max_count=0
max_word=""
for i in words:
      count=0
      for j in words:
            if i==j:
                  count+=1
      if count>=2:
            lst.append(i)
      if count>max_count:
            max_count=count
            max_word=i
            print(max_count, max_word)
print(max_word)    # слово 'можно' встречается в тексте 3 раза       
            
      

#4)Отберите все ссылки
pat=re.compile("\S+.ru | \S+.ru\S+")
s=pat.findall(text)
print(s)

#5)Самый популярный домен в тексте
print("ru=",re.findall("ru",text))
print("com=",re.findall("com",text))

#6)Замените все ссылки
text=re.sub(pat,"Ссылка отобразится после регистрации ",text)





