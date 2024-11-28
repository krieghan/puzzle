from game_common import canvas

import bishops_world


def main():
    world = bishops_world.BishopsWorld()
    bishops_canvas = canvas.Canvas(
            world=world,
            title='Bishops')
    world.set_canvas(bishops_canvas)
    bishops_canvas.start()


if __name__ == '__main__':
    main()

