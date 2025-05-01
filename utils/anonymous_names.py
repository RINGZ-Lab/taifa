import random

def generate_anonymous_name():
    colors = ["Red", "Blue", "Green", "Yellow", "Purple", "Orange", "Pink", "Cyan", "Brown", "Gray"]
    animals = ["Panda", "Tiger", "Lion", "Eagle", "Dolphin", "Wolf", "Bear", "Fox", "Owl", "Hawk"]
    
    return f"{random.choice(colors)}{random.choice(animals)}"