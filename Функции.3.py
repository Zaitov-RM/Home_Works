name=str(input("Введите имя игрока №1 "))
player={"name":name,"damage":20,"health":100}

name=str(input("Введите имя игрока №2 "))
enemy={"name":name,"damage":50,"health":100}

print(player["name"])
print(enemy["name"])

def attack(player1,player2):
      player2["health"]= player2["health"]-player1["damage"]

attack(player,enemy)
print("Enemy health="+str(enemy["health"]))
attack(player,enemy)
print("Enemy health="+str(enemy["health"]))
