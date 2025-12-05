from threading import Thread


def square():
    for i in range(1, 11):
        print(i**2)

def cube():
    for i in range(1, 11):
        print(i**3)


if __name__ == "__main__":
    th_square = Thread(target=square())
    th_cube = Thread(target=cube())

    th_square.start()
    th_cube.start()

    th_square.join()
    th_cube.join() 
    
    