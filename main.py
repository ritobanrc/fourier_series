import sys
import cmath
import numpy as np

from vispy import app, visuals

class Canvas(app.Canvas):
    def __init__(self):
        app.Canvas.__init__(self, keys='interactive', size=(800, 800), resizable=False)

        self.time = 0
        # dictionary from n to c_n
        self.coeffs = {}
        self.ellipses = {}
        self.arrows = {}
        self.ns = list(range(-21, 22, 2))
        assert self.ns[0] % 2 == 1
        assert self.ns[0]  == -self.ns[-1]
        for n in self.ns:
            if n == 0:
                c_n = 0
            else:
                c_n = -2j/(n*cmath.pi)

            (r, phi) = cmath.polar(c_n)
            self.ellipses[n] = visuals.EllipseVisual(
                center=(0, 0),
                color=(0, 0, 0, 0),
                border_color=(0.5, 0.5, 0.5, 1.0),
                radius=(r, r)
            )
            self.ellipses[n].transform = visuals.transforms.STTransform((0.5, 0.5, 0.5))
            self.arrows[n] = visuals.ArrowVisual(pos=np.zeros((2, 2)),
                                                 color=(1.0, 1.0, 1.0, 1.0),
                                                 method='gl')
            self.arrows[n].transform = visuals.transforms.STTransform((0.5, 0.5, 0.5))

            self.coeffs[n] = c_n

        self.ns.sort(key=lambda n: cmath.polar(self.coeffs[n])[0], reverse=True)

        self.line = visuals.LineVisual(pos=np.zeros((1, 2)),
                                       color=(1.0, 1.0, 0.0, 1.0),
                                       width=2,
                                       method='gl'
                                       )
        self.line.transform = visuals.transforms.STTransform((0.5, 0.5, 0.5))

        self._timer = app.Timer('auto', connect=self.on_timer, start=True)
        self.show()

    def on_draw(self, ev):
        self.context.set_clear_color((0.1, 0.1, 0.1, 1.0))
        self.context.set_viewport(0, 0, *self.physical_size)
        self.context.clear()
        for _, ellipse in self.ellipses.items():
            ellipse.draw()
        for _, arrow in self.arrows.items():
            arrow.draw()
        self.line.draw()

    def on_resize(self, event):
        vp = (0, 0, *self.physical_size)
        self.context.set_viewport(*vp)

    def on_timer(self, event):
        self.time += 0.005
        end_point = 0 + 0j
        for n in self.ns:
            self.ellipses[n].center = (end_point.real, end_point.imag)
            temp = end_point
            end_point += self.coeffs[n] * cmath.exp(n*cmath.tau*1j*self.time)
            self.arrows[n].set_data(np.array([[temp.real, temp.imag],
                                              [end_point.real, end_point.imag]]))

        new_line = np.vstack((self.line.pos + np.array([0, 0.01]), [end_point.real, end_point.imag]))
        self.line.set_data(new_line)
        self.update()

if __name__ == '__main__':
    win = Canvas()
    if sys.flags.interactive != 1:
        win.app.run()

