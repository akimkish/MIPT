from threading import Thread
import time

def print_number(num: int):
    for i in range(1,11):
        print(f"Thread {num} - {i}")
        time.sleep(1)
 

if __name__ == "__main__":
    thr1 = Thread(target=print_number, args=(1, ))
    thr2 = Thread(target=print_number, args=(2, ))
    thr3 = Thread(target=print_number, args=(3, ))

    thr1.start()
    thr2.start()
    thr3.start()
    print("Threads are starting")
    thr1.join()
    thr2.join()
    thr3.join()
    print("Threads are finished")