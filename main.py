import sys
import cmath
import numpy as np

from vispy import app, visuals
from scipy.signal import square
import scipy.integrate as integrate
from svgpathtools import svg2paths

shift_up = False

def get_square_wave_coeff(n):
    if n == 0: return 0
    else:      return -2j/(n*cmath.pi)


class Canvas(app.Canvas):
    def __init__(self, svg='treble.svg', num_samples=1000, follow_path=True):
        app.Canvas.__init__(self, keys='interactive', size=(800, 800), resizable=False)

        self.time = 0
        # dictionary from n to c_n
        self.coeffs = {}
        self.ellipses = {}
        self.arrows = {}
        self.ns = list(range(-10, 10))

        paths, _, svg_attribs = svg2paths(svg, return_svg_attributes=True)
        *_, width, height = [int(x) for x in svg_attribs['viewBox'].split(' ')]
        if len(paths) > 1:
            print("Warning: SVG contains multiple paths, but only 1 is supported. Using only first path.")
        path = paths[0]
        assert path.isclosed()

        dt = 1/num_samples

        ts = np.linspace(0, 1, num_samples)
        samples = np.empty([num_samples], dtype=complex)
        for i, t in enumerate(ts):
            p = path.point(t)
            samples[i] = p.real/width + -1j * p.imag / height

        self.camera = visuals.transforms.STTransform([0.5, 0.5, 0.5])

        for n in self.ns:
            # c_n = np.array([cmath.exp(-n*cmath.tau*1j*t)*cs
            # for t, cs, in zip(ts, samples)
            # ]).sum() * dt
            c_n = np.sum(np.exp(-n*cmath.tau*1j*ts)*samples) * dt
            (r, phi) = cmath.polar(c_n)
            self.ellipses[n] = visuals.EllipseVisual(
                center=(0, 0),
                color=(0, 0, 0, 0),
                border_color=(0.5, 0.5, 0.5, 1.0),
                radius=(r, r)
            )
            self.ellipses[n].transform = self.camera
            self.arrows[n] = visuals.ArrowVisual(pos=np.zeros((2, 2)),
                                                 color=(1.0, 1.0, 1.0, 1.0),
                                                 method='gl')
            self.arrows[n].transform = self.camera

            self.coeffs[n] = c_n

        self.ns.sort(key=lambda n: cmath.polar(self.coeffs[n])[0], reverse=True)

        self.line = visuals.LineVisual(pos=np.zeros((1, 2)),
                                       color=(1.0, 1.0, 0.0, 1.0),
                                       width=2,
                                       method='gl',
                                       # antialias=True
                                       )
        self.line.transform = self.camera

        self._timer = app.Timer('auto', connect=self.on_timer, start=True)
        self.context.set_clear_color((0.1, 0.1, 0.1, 1.0))
        self.show()

    def on_draw(self, ev):
        # self.context.set_viewport(0, 0, *self.physical_size)
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
        self.time += 0.001
        end_point = 0 + 0j
        for n in self.ns:
            self.ellipses[n].center = (end_point.real, end_point.imag)
            temp = end_point
            end_point += self.coeffs[n] * cmath.exp(n*cmath.tau*1j*self.time)
            self.arrows[n].set_data(np.array([[temp.real, temp.imag],
                                              [end_point.real, end_point.imag]]))

        if shift_up:
            new_line = self.line.pos + np.array([0, 0.01])
        else:
            new_line = self.line.pos
        if new_line.shape[0] == 1:
            new_line[0] = [end_point.real, end_point.imag]
        new_line = np.vstack((new_line, [end_point.real, end_point.imag]))
        self.line.set_data(new_line)

        # if follow_path:
        # self.camera = visuals.transforms.

        self.update()

    @property
    def canvas_tr(self):
        return visuals.transforms.STTransform.from_mapping(
            [(0, 0), self.size],
            [(-1, 1), (1, -1)])

    def on_mouse_move(self, event):
        """Mouse move handler
        Parameters
        ----------
        event : instance of Event
            The event.
        """
        if event.is_dragging:
            dxy = event.pos - event.last_event.pos
            button = event.press_event.button

            if button == 1:
                dxy = self.canvas_tr.map(dxy)
                o = self.canvas_tr.map([0, 0])
                t = dxy - o
                self.camera.move(t)
            elif button == 2:
                center = self.canvas_tr.map(event.press_event.pos)
                if self.camera._aspect is None:
                    self.camera.zoom(np.exp(dxy * (0.01, -0.01)), center)
                else:
                    s = dxy[1] * -0.01
                    self.camera.zoom(np.exp(np.array([s, s])), center)


    def on_mouse_wheel(self, event):
        zoom = np.exp(-event.delta[1] * -0.1)
        self.camera.zoom([zoom, zoom], self.canvas_tr.map(event.pos))

if __name__ == '__main__':
    canvas = Canvas()
    canvas.app.run()

