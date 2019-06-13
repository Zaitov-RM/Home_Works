#Декоратор
def mylog(func):
      def wrapper(*args, **kwargs):
            res=func(*args, **kwargs)
            try:
                  with open(r'log\deco.log','a',encoding='utf-8') as f:
                        f.write(f'{func.__name__}-{args}-{kwargs}')
                        f.write("\n")
            except:
                  with open(r'log\deco.log', 'w', encoding='utf-8') as f:
                        f.writelines(f'{func.__name__}-{args}-{kwargs}')
            return res
      return wrapper
if __name__=='__main__':
      @mylog
      def my_func(x,y):
            return x+y

      my_func(10,11)

            
      
