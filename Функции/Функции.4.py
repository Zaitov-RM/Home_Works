name=str(input("Введите имя игрока №1 "))
player={"name":name,"damage":40,"health":100,"armor":3}

name=str(input("Введите имя игрока №2 "))
enemy={"name":name,"damage":50,"health":100,"armor":2}

print(player["name"])
print(enemy["name"])

def attack(player1,player2):
      player2["health"]= player2["health"]-dam_arm(player1,player2)


def dam_arm(player1,player2):
      return player1["damage"]/player2["armor"]

attack(player,enemy)
print("Player1 damage="+str(player["damage"]))
print("Player2 health="+str(enemy["health"]))

