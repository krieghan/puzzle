from game_common import canvas

import piano_world

def flatten(*args):
    l = []
    for arg in args:
        if isinstance(arg, tuple):
            l.extend(arg)
        else:
            l.append(arg)
    return l


def main():
    world = piano_world.PianoWorld()
    piano_canvas = canvas.Canvas(
            world=world,
            title='Piano')
    world.set_canvas(piano_canvas)
    piano_canvas.start()




if __name__ == '__main__':
    main()
