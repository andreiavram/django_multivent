__author__ = 'yeti'

import datetime
from io import StringIO

import svgwrite

import cairocffi
cairocffi.install_as_pycairo()

import cairosvg
from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF





class DrawingToMemory(svgwrite.Drawing):
    def save_to_buffer(self):
        svg_buffer = self.draw_to_buffer()
        svg = svg_buffer.getvalue()
        svg_buffer.close()
        return svg

    def draw_to_buffer(self):
        svg_buffer = StringIO()
        self.write(svg_buffer)
        svg_buffer.seek(0)
        return svg_buffer

    def save_to_fileobject(self, file_object):
        self.write(file_object)
        return file_object


class Event(object):
    def __init__(self, dates, rgb_color, name):
        self.start_date = dates[0]
        self.end_date = dates[1]
        self.dates = dates
        self._rgb_color = rgb_color
        self.background_color = svgwrite.rgb(*rgb_color)
        self.name = name
        self.slot = None

    @property
    def text_color(self):
        r, g, b = self._rgb_color
        a = 1. - (0.299 * r + 0.587 * g + 0.114 * b) / 255.
        _d = 0 if a < 0.5 else 255
        return svgwrite.rgb(_d, _d, _d)

    def get_rect_style(self):
        return _make_style(*self._rgb_color)

    def get_text_style(self):
        return dict(font_family="Ubuntu",
                    font_size="5mm",
                    fill=self.text_color)

MAX_EVENTS = 5
EVENT_HEIGHT = 10   # mm
FONT_NAME = "Ubuntu"

A0_size = (1189, 841)


class EventRenderer(object):
    @staticmethod
    def date_in_range(date_to_check, range_to_check):
        return range_to_check[0] <= date_to_check <= range_to_check[1]


class PlannerRenderer(EventRenderer):
    @staticmethod
    def add_mm_to_sizes(size):
        if isinstance(size, basestring) or isinstance(size, int) or isinstance(size, float):
            return "%smm" % size
        return "%dmm" % size[0], "%dmm" % size[1]

    @staticmethod
    def _make_style(r, g, b):
        return dict(stroke=svgwrite.rgb(10, 10, 16),
                    stroke_width="0.5mm",
                    fill=svgwrite.rgb(r, g, b))

    def __init__(self, events=None, **kwargs):
        self.events = events

    def get_planner(self, year=None, output_format="buffer", file_format="svg", filename=None):
        if year is None:
            year = datetime.date.today().year

        dwg = DrawingToMemory(filename, size=self.add_mm_to_sizes(A0_size), profile="tiny")

        # TODO: center stuff
        date_rect_pos = (10, 10)
        date_rect_size = (30, 64)

        date_rect_style = self._make_style(200, 200, 200)
        date_rect_style_weekend = self._make_style(244, 44, 440)
        style_vacante = self._make_style(208, 255, 156)

        special_dates = (((datetime.date(2015, 2, 2), datetime.date(2015, 2, 6)), style_vacante),
                         ((datetime.date(2015, 6, 15), datetime.date(2015, 8, 31)), style_vacante))

        events = [Event((datetime.date(2015, 8, 15), datetime.date(2015, 8, 24)), (255, 255, 89), "CCL2015"),
                  Event((datetime.date(2015, 3, 15), datetime.date(2015, 5, 15)), (240, 37, 89), "TEST LONG EVENT"),
                  Event((datetime.date(2015, 3, 18), datetime.date(2015, 4, 20)), (37, 89, 240), "TEST OVERRIDE"),
                  Event((datetime.date(2015, 2, 18), datetime.date(2015, 3, 20)), (37, 89, 240), "TEST OVERRIDE 2 "),
                  Event((datetime.date(2015, 3, 22), datetime.date(2015, 3, 25)), (255, 255, 89), "TEST OVERRIDE 3")]

        events.sort(key=lambda x: x.start_date)

        month_names = ["Ian", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]

        for month in range(1, 13):
            date_start = datetime.date(year, month, 1)
            month_offset = date_start.weekday()
            date_rect_pos = (date_rect_pos[0] + date_rect_size[0] * month_offset, date_rect_pos[1])

            if month == 12:
                date_end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                date_end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            date_range = [date_start + datetime.timedelta(days=i) for i in range(0, (date_end - date_start).days + 1)]
            date_events = {date: [i for i in range(1, MAX_EVENTS + 1)] for date in date_range}

            month_text_position = (date_rect_pos[0] - date_rect_size[0] / 2, date_rect_pos[1] + 0.33 * date_rect_size[1])
            dwg.add(dwg.text("%s" % month_names[month - 1],
                             insert=self.add_mm_to_sizes(month_text_position),
                             font_family=FONT_NAME,
                             font_size=self.add_mm_to_sizes(8),
                             text_anchor="middle"))

            for day in date_range:
                style = date_rect_style
                for special_style in special_dates:
                    if self.date_in_range(day, special_style[0]):
                        style = special_style[1]
                style = style if day.weekday() < 5 else date_rect_style_weekend

                grp = dwg.g()
                grp.add(dwg.rect(insert=self.add_mm_to_sizes(date_rect_pos), size=self.add_mm_to_sizes(date_rect_size), **style))

                day_text_position = (date_rect_pos[0] + date_rect_size[0] * 0.75,
                                     date_rect_pos[1] + 0.90 * date_rect_size[1])

                grp.add(dwg.text("%s" % day.day,
                                 insert=self.add_mm_to_sizes(day_text_position),
                                 font_family=FONT_NAME,
                                 font_size=self.add_mm_to_sizes(8),
                                 text_anchor="middle"))

                date_rect_pos = (date_rect_pos[0] + date_rect_size[0], date_rect_pos[1])
                dwg.add(grp)

            for event in events:
                if self.date_in_range(date_range[0], event.dates) \
                        or self.date_in_range(date_range[-1], event.dates) \
                        or date_range[0] <= event.start_date <= date_range[-1] \
                        or date_range[0] <= event.end_date <= date_range[-1]:

                    event_start_date = max(date_range[0], event.start_date)
                    event_end_date = min(date_range[-1], event.end_date)

                    event_days = [d for d in date_range if event_start_date <= d <= event_end_date]

                    if any([len(date_events[date]) > MAX_EVENTS for date in event_days]):
                        raise Exception("Too many events for month %s" % month_names[month - 1])

                    for date in event_days:
                        if event not in date_events[date]:
                            date_events[date].append(event)

                    if event.slot is None:
                        start_set = set(date_events[event_days[0]])
                        for day in event_days:
                            start_set = start_set & set(date_events[day])
                        start_set = sorted(list(start_set))
                        if len(start_set) == 0:
                            raise Exception("Not enough place to place event in month %s" % month_names[month - 1])
                        event.slot = start_set[0]

                    for day in event_days:
                        date_events[day].remove(event.slot)

                    event_x = (month_offset + event_start_date.day - 1) * date_rect_size[0] + 10
                    event_width = ((event_end_date-event_start_date).days + 1) * date_rect_size[0]
                    grp = dwg.g()

                    event_position = (event_x, date_rect_pos[1] + (event.slot - 1) * EVENT_HEIGHT)
                    grp.add(dwg.rect(insert=self.add_mm_to_sizes(event_position),
                                     size=self.add_mm_to_sizes((event_width, EVENT_HEIGHT)), **event.get_rect_style()))

                    event_text_position = (event_x + 3, date_rect_pos[1] + (event.slot - 1) * EVENT_HEIGHT + 7)
                    grp.add(dwg.text(event.name, insert=self.add_mm_to_sizes(event_text_position), **event.get_text_style()))
                    dwg.add(grp)

            date_rect_pos = (10, date_rect_pos[1] + date_rect_size[1])

        # can use save_to_buffer() to get buffer.value()
        # can use save_to_fileobject(response) to write directly to response
        if output_format == "buffer":
            svg = dwg.draw_to_buffer()
            svg_bytestring = svg.getvalue()
            svg.close()
            if file_format == "svg":
                return svg_bytestring
            elif file_format == "pdf":
                pdf = cairosvg.svg2pdf(svg_bytestring)
                return pdf
            elif file_format == "png":
                png = cairosvg.svg2png(svg_bytestring)
                return png
        if output_format == "file":
            if file_format == "svg":
                dwg.save()
            if file_format == "pdf":
                pdf = svg2rlg(filename)
                renderPDF.drawToFile(pdf, filename + ".pdf")
        return

if __name__ == "__main__":
    FILE_NAME = "test.svg"
    PDF_FILE_NAME = FILE_NAME + ".pdf"
    planner = PlannerRenderer()
    planner.get_planner(output_format="file", filename=FILE_NAME)