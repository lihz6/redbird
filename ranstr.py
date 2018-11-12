from string import ascii_letters
from string import digits
from random import sample
from random import choice
from random import seed

letters = sample(digits+ascii_letters, 62)


def random():
    return ''.join(choice(letters) for _ in range(9))


if __name__ == '__main__':
    keys = set()
    for _ in range(1000000):
        key = random()
        if key in keys:
            raise Exception(key)
        keys.add(key)
