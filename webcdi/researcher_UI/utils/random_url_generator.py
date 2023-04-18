import  random


def random_url_generator(size=64, chars="0123456789abcdef"):  # Function for generating a string of random characters from a set. Meant for generating unique URLs for each administration.
    return "".join(random.choice(chars) for _ in range(size))
