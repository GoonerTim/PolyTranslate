# This is a sample Ren'Py script file for testing

define e = Character("Eileen", color="#c8ffc8")
define mc = Character("Player")

label start:
    scene bg room

    e "Hello! Welcome to the game."
    e "How are you feeling today?"

    mc "I'm doing great, thanks for asking!"

    menu:
        "Tell me more about this place":
            jump info_route
        "I want to explore":
            jump explore_route
        "Goodbye":
            jump ending

label info_route:
    e "This is a wonderful place full of adventures."
    _("This is a translatable string")
    jump ending

label explore_route:
    e "Feel free to look around!"
    $ explored = True
    jump ending

label ending:
    e "Thanks for playing!"
    return
