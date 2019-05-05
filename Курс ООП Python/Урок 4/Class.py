'''
1. Создайте класс Word.
2. Добавьте свойства text и part of speech.
3. Добавьте возможность создавать объект слово со значениями в скобках.
4. Создайте класс Sentence
5. Добавьте свойство content, равное списку, состоящему из номеров слов, входящих в предложение.
6. Добавьте метод show, составляющий предложение.
7. Добавьте метод show_parts, отображающий, какие части речи входят в предложение.
'''


class Word:
      text="Кодить"
      part_of_speech="Глагол"
     
      def __init__(self,text,pof):
            self.text=text
            self.part_of_speech=pof

my_word=Word("Хорошо","Наречие")
print(my_word.text, my_word.part_of_speech)
print("-"*80)


class Sentence:
      text={}
      content=[]
      sentence=""
      words=[]
      pof=[]#part_of_speech
      
      def __init__(self,text, content):
            self.text=text
            self.content=content
            self.split()

      #Делит словарь на 2 списка: слов и частей речи     
      def split(self):

            for i in self.text.keys():
                  self.words.append(i)
            for i in self.words:
                  self.pof.append(self.text[i])

      def show(self):
            for i in self.content:
                  if self.sentence:
                        self.sentence=self.sentence +" "+str(self.words[i-1])
                  else:
                        self.sentence=str(self.words[i-1])
            return self.sentence

      def part_of_speech(self):
            lst=[]
            for i in self.content:
                  lst.append(self.pof[i-1])
            return lst
                  


text={'car':"существительное",'drive':"глагол",'I':"существительное",'like':"глагол",'to':"артикл"}
content=[3,4,5,2,1]
sent=Sentence(text,content)

print(sent.show())
print(sent.part_of_speech())







            

