allowed_nums_of_faces = [4, 6, 8, 10, 12, 20]


def roll(update, context):
    command, *message = update.message.text.lower().split(" ")
    dice = " ".join(message)
    num_of_dice, right = dice.split("d")
    num_of_faces = 0
    bonus = 0
    if "+" in right or "-" in right:
        i = max(right.find("+"), right.find("-"))
        num_of_faces = int(right[:i])
        bonus = int(num_of_faces[i:])
    num_of_dice = int(num_of_dice)

    if num_of_faces not in allowed_nums_of_faces:
        return

    results = list()

    for i in range(num_of_dice):
        pass
