import requests
import json

while True:
      try:
            city=str(input("Введите город "))

            link="https://www.travelpayouts.com/widgets_suggest_params?q=Из%20Москвы%20в%20"+city
            req=requests.get(link)
            data=json.loads(req.text)

            print(city, data["destination"]["iata"])
      except KeyError:
            print("Нет такого города")
            continue
