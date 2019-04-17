
#1 Вариант
def Max(a,b,c):
      if a>b:
            if a>c:
                  return a
            else:
                  return c
      else:
            a=b
            if a>c:
                  return a
            else:
                  return c

print(Max(3,4,5))

#2 Вариант
def Max2(a,b):
      if a>b:
            return a
      else:
            return b
print(Max2(Max2(3,4),5))
