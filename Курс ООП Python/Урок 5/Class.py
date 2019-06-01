'''
1. Создайте классы Noun и Verb.
2. Настройте наследование от Word.
3. Добавьте защищенное свойство «Грамматические характеристики».
4. Перестройте работу метода show класса Sentence.
5. Перестройте работу метода show_part класса Sentence, чтобы он показывал грамматические характеристики.
'''


#---------------Class Word
class Word:
      text="Кодить"
      part_speech="Глагол"
      word_list=[]
     
      def __init__(self,text,pof):
            self.text=text
            self.part_speech=pof
            self.word_list=[self.text,self.part_speech]

#----------------Class Noun
class Noun(Word):
      _gram_char=[]

      def __init__(self,text,pof="noun",gram_char=[]):
            super().__init__(text,pof)
            self.gram_char=['genus','numerus','person','casus']
            self.word_list.append(self.gram_char)

      def show(self):
            return self.gram_char
         
            
#----------------Class Verb
class Verb(Word):
      _gram_char=[]

      def __init__(self,text,pof="verb",gram_char=[]):
            super().__init__(text,pof)
            self.gram_char=['залог','спряжение','число','род','возратность']
            self.word_list.append(self.gram_char)
            
      def show(self):
            return self.gram_char

#---------------Class Sentence
class Sentence:
      text=[]
      content=[]

      def __init__(self,text, content):
            self.text=text
            self.content=content

      def show(self):
            sentence=''
            for i in self.content:
                  if sentence:
                        sentence=sentence +" "+str(self.text[i-1].text)
                  else:
                        sentence=str(self.text[i-1].text)
            return sentence

      def part_of_speech(self):
            for i in self.content:
                  print(self.text[i-1].text,end=" ")
                  print(self.text[i-1].word_list[2])
            
                  
#---------------------------------------------------------------------


text=[Noun("I"),Verb("go"),Noun("home"),Noun("bread"),Verb("eat")]
content=[1,5,4]#I eat bread

sent=Sentence(text,content)

print(sent.show())
sent.part_of_speech()







            

