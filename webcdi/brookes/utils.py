import random
import string


def create_brookes_code(length=15):
    # choose from all lowercase letter
    letters = string.ascii_uppercase + string.digits
    letters.replace("I", "").replace("O", "")
    result_str = "".join(random.choice(letters) for i in range(length))
    return result_str
