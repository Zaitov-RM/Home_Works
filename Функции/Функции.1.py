def info(name,age,city):
      year=""
      if int(age)%10==1:
            year="год"
      elif 2<=int(age)%10<=4:
            year="года"
      else:
            year="лет"
      return name+" ,"+age+" "+year+", проживает в городе "+city
Name=input("Name ")
Age=input("Age ")
City=input("City ")

print(info(Name,Age,City))
