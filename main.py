import cmath
import numpy as np
import cairo
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib, Gdk
from svgpathtools import svg2paths

freqs =  list(range(-200, 200))
shift_up = False

time = 0
line = []
coeffs = {}
camera_scale = (0.5, 0.5)

def load_square_wave():
    for n in freqs:
        if n % 2 == 0:
            coeffs[n] = 0
        else:
            coeffs[n] = -2j/(n*cmath.pi)


def load_svg_coeffs(filename, num_samples=10000):
    paths, _, svg_attribs = svg2paths(filename, return_svg_attributes=True)
    if 'viewBox' in svg_attribs:
        *_, width, height = [int(float(x)) for x in svg_attribs['viewBox'].split(' ')]
    else:
        width = int(float(svg_attribs['width']))
        height = int(float(svg_attribs['height']))
    if len(paths) > 1:
        print("Warning: SVG contains multiple paths, but only 1 is supported. Using only first path.")
    path = paths[0]

    dt = 1/num_samples

    ts = np.linspace(0, 1, num_samples)
    samples = np.empty([num_samples], dtype=complex)
    for i, t in enumerate(ts):
        p = path.point(t)
        samples[i] = p.real/width + 1j * p.imag / height

    for n in freqs:
        coeffs[n] = np.sum(np.exp(-n*cmath.tau*1j*ts)*samples) * dt


def draw(da, ctx):
    """
    The draw loop. Called once per frame and draws stuff
    """
    global time
    alloc = da.get_allocation()
    width = alloc.width
    height = alloc.height

    ctx.scale(camera_scale[0]*width/2, camera_scale[1]*height/2)
    ctx.translate(2, 2)
    ctx.set_line_width(0.003)

    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()

    end_point = 0 + 0j
    for n in freqs:
        # self.ellipses[n].center = (end_point.real, end_point.imag)
        ctx.set_source_rgb(0.4, 0.4, 0.5)
        radius, _ = cmath.polar(coeffs[n])
        ctx.arc(end_point.real, end_point.imag, radius, 0, cmath.tau)
        ctx.stroke()
        ctx.move_to(end_point.real, end_point.imag)

        end_point += coeffs[n] * cmath.exp(n*cmath.tau*1j*time)

        ctx.set_source_rgb(0.8, 0.8, 0.8)
        ctx.line_to(end_point.real, end_point.imag)
        ctx.stroke()

    if shift_up:
        for idx, _ in enumerate(line):
            line[idx][1] += 0.005

    line.append([end_point.real, end_point.imag])

    ctx.set_source_rgb(1.0, 1.0, 0)
    for point in line:
        ctx.line_to(*point)
    ctx.stroke()

    time += 0.002


def zoom(da, event):
    global camera_scale
    # print(event.x, event.y, event.direction)
    if event.direction == Gdk.ScrollDirection.UP:
        camera_scale = (camera_scale[0]*1.25, camera_scale[1]*1.25)
    elif event.direction == Gdk.ScrollDirection.DOWN:
        camera_scale = (camera_scale[0]*0.8, camera_scale[1]*.8)

def main():
    """
    The main function
    """
    win = Gtk.Window()
    win.connect('destroy', Gtk.main_quit)
    win.set_default_size(800, 800)

    drawingarea = Gtk.DrawingArea()
    win.add(drawingarea)
    drawingarea.connect('draw', draw)
    drawingarea.add_events(Gdk.EventMask.SCROLL_MASK)
    drawingarea.connect('scroll-event', zoom)

    def tick():
        drawingarea.queue_draw()
        return True
    GLib.timeout_add(20, tick)

    load_svg_coeffs('treble.svg')

    freqs.sort(key=lambda n: cmath.polar(coeffs[n])[0], reverse=True)

    win.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
