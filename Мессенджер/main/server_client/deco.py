#Декоратор
def log(func):
      def wrapper(*args, **kwargs):
            res=func(*args, **kwargs)
            with open('deco.log','w',encoding='utf-8') as f:
                  f.write(f'{func.__name__}-{args}-{kwargs}')
            return res
      return wrapper
if __name__=='__main__':
      @log
      def my_func(x,y):
            return x+y

      my_func(10,11)

            
      
