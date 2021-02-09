import time

if __name__ == '__main__':
    str1 = '1612522780434'
    print(time.time())
    print(time.localtime(float(str1)/1000))
    print(time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(str1)/1000)))