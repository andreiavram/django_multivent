from multivent.events import Event

__author__ = 'yeti'

import datetime
from io import StringIO

import svgwrite

import cairocffi
cairocffi.install_as_pycairo()

import cairosvg


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


class PlannerEventStyle(object):
    def __init__(self, color=(0, 0, 0), background_color=(255, 255, 255), font_name="Ubuntu", text_size=5,
                 stroke_width=0.5, stroke_color=(10, 10, 10)):

        self.color = svgwrite.rgb(*color)
        self.background_color = svgwrite.rgb(*background_color)
        self.stroke_color = svgwrite.rgb(*stroke_color)

        self._rgb_color = color
        self._rgb_background_color = background_color
        self._rgb_stroke_color = stroke_color
        self.font_name = font_name
        self.text_size = text_size
        self.stroke_width = stroke_width

    @property
    def contrast_color(self):
        r, g, b = self._rgb_background_color
        a = 1. - (0.299 * r + 0.587 * g + 0.114 * b) / 255.
        _d = 0 if a < 0.5 else 255
        return svgwrite.rgb(_d, _d, _d)

    @classmethod
    def make_size(cls, val):
        return PlannerRenderer.add_mm_to_sizes(val)

    def get_text_style(self):
        return dict(font_family=self.font_name, font_size=self.make_size(self.text_size), fill=self.color)

    def get_rect_style(self):
        return self._make_style(self.background_color)

    def _make_style(self, fill_color):
        return dict(stroke=svgwrite.rgb(10, 10, 16),
                    stroke_width=self.make_size(self.stroke_width),
                    fill=fill_color)


class PlannerEvent(Event):
    def __init__(self, dates, name, **kwargs):
        super(PlannerEvent, self).__init__(dates, name, **kwargs)
        self.slot = None
        self.style = kwargs.get("style", None)
        self.event_type = kwargs.get("event_type")

        if self.style is None:
            self.style = PlannerEventStyle()


class EventRenderer(object):
    @staticmethod
    def date_in_range(date_to_check, range_to_check):
        return range_to_check[0] <= date_to_check <= range_to_check[1]


class PlannerRenderer(EventRenderer):
    DEFAULT_SIZES = {
        "A0": (1189, 841)
    }

    supported_event_types = ["normal", "background", "special_date", "weekend", "empty"]

    def __init__(self, events=None, page_size="A0", max_events=5, font_name="Ubuntu", event_height=10,
                 default_styles=None, month_name_font_size=8, day_name_font_size=8):
        self.page_size = self.DEFAULT_SIZES.get(page_size, self.DEFAULT_SIZES["A0"])
        self.max_day_events = max_events
        self.font_name = font_name
        self.event_height = event_height
        self.events = events
        self.month_name_font_size = month_name_font_size
        self.day_name_font_size = day_name_font_size

        if default_styles is None:
            default_styles = {}

        styles = self.get_default_styles()
        for e in self.supported_event_types:
            if e not in default_styles.keys():
                default_styles[e] = styles.get(e)

        self.default_styles = default_styles

    @classmethod
    def get_default_styles(cls):
        styles = {
            "normal": PlannerEventStyle(background_color=(255, 255, 255)),
            "background": PlannerEventStyle(background_color=(208, 255, 156)),
            "weekend": PlannerEventStyle(background_color=(244, 44, 440)),
            "special_date": PlannerEventStyle(color=(255, 44, 44)),
            "empty": PlannerEventStyle()
        }
        return styles

    @staticmethod
    def add_mm_to_sizes(size, fallthrough=True):
        if fallthrough:
            return size

        if isinstance(size, basestring) or isinstance(size, int) or isinstance(size, float):
            return "%smm" % size
        return "%dmm" % size[0], "%dmm" % size[1]

    def get_planner(self, year=None, output_format="buffer", file_format="svg", filename=None):
        if year is None:
            year = datetime.date.today().year

        dwg = DrawingToMemory(filename, size=self.add_mm_to_sizes(self.page_size, False), viewBox=("0 0 %s %s" % (self.page_size[0], self.page_size[1])), profile="tiny")

        #   should this be moved somewhere else?
        date_rect_size = (30, 64)
        centering_offset_y = (self.page_size[1] - 12 * date_rect_size[1]) / 2
        centering_offset_x = (self.page_size[0] - 37 * date_rect_size[0]) / 2
        date_rect_pos = (centering_offset_x, centering_offset_y)

        self.events.sort(key=lambda x: x.start_date)
        style_weekday = self.default_styles.get("normal")
        style_weekend = self.default_styles.get("weekend")

        month_names = ["Ian", "Feb", "Mar", "Apr", "Mai", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]

        background_events = [e for e in self.events if e.event_type == "background"]
        background_events.sort(key=lambda x: (x.start_date, x.end_date))
        for month in range(1, 13):
            date_start = datetime.date(year, month, 1)
            month_offset = date_start.weekday()
            date_rect_pos = (date_rect_pos[0] + date_rect_size[0] * month_offset, date_rect_pos[1])

            if month == 12:
                date_end = datetime.date(year + 1, 1, 1) - datetime.timedelta(days=1)
            else:
                date_end = datetime.date(year, month + 1, 1) - datetime.timedelta(days=1)

            date_range = [date_start + datetime.timedelta(days=i) for i in range(0, (date_end - date_start).days + 1)]
            date_events = {date: [i for i in range(1, self.max_day_events + 1)] for date in date_range}

            month_text_position = (date_rect_pos[0] - date_rect_size[0] / 5, date_rect_pos[1] + .9 * date_rect_size[1])
            month_text = dwg.text("%s %s" % (month_names[month - 1], year),
                              insert=self.add_mm_to_sizes(month_text_position),
                              font_family=self.font_name,
                              font_size=self.add_mm_to_sizes(self.month_name_font_size),)
            dwg.add(month_text)
            print month_text_position
            month_text.rotate(-90, center=month_text_position)

            for day in date_range:
                style = style_weekday
                for e in background_events:
                    if self.date_in_range(day, (e.start_date, e.end_date)):
                        style = e.style if e.style is not None else self.default_styles("background")
                    if e.start_date > day:
                        break

                style = style if day.weekday() < 5 else style_weekend

                grp = dwg.g()
                grp.add(dwg.rect(insert=self.add_mm_to_sizes(date_rect_pos),
                                 size=self.add_mm_to_sizes(date_rect_size),
                                 **style.get_rect_style()))

                day_text_position = (date_rect_pos[0] + date_rect_size[0] * 0.75,
                                     date_rect_pos[1] + 0.90 * date_rect_size[1])

                grp.add(dwg.text("%s" % day.day,
                                 insert=self.add_mm_to_sizes(day_text_position),
                                 font_family=self.font_name,
                                 font_size=self.add_mm_to_sizes(self.day_name_font_size),
                                 text_anchor="middle"))

                date_rect_pos = (date_rect_pos[0] + date_rect_size[0], date_rect_pos[1])
                dwg.add(grp)

            foreground_events = [e for e in self.events if e.event_type == "normal"]
            for event in foreground_events:
                if self.date_in_range(date_range[0], event.dates) \
                        or self.date_in_range(date_range[-1], event.dates) \
                        or date_range[0] <= event.start_date <= date_range[-1] \
                        or date_range[0] <= event.end_date <= date_range[-1]:

                    event_start_date = max(date_range[0], event.start_date)
                    event_end_date = min(date_range[-1], event.end_date)

                    event_days = [d for d in date_range if event_start_date <= d <= event_end_date]

                    if any([len(date_events[date]) > self.max_day_events for date in event_days]):
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

                    event_x = (month_offset + event_start_date.day - 1) * date_rect_size[0] + centering_offset_x
                    event_width = ((event_end_date-event_start_date).days + 1) * date_rect_size[0]
                    grp = dwg.g()

                    event_position = (event_x, date_rect_pos[1] + (event.slot - 1) * self.event_height)
                    grp.add(dwg.rect(insert=self.add_mm_to_sizes(event_position),
                                     size=self.add_mm_to_sizes((event_width, self.event_height)),
                                     **event.style.get_rect_style()))

                    # todo: improve text position here
                    event_text_position = (event_x + self.event_height / 3.,
                                           date_rect_pos[1] + (event.slot - 1 + 0.7) * self.event_height)
                    grp.add(dwg.text(event.name,
                                     insert=self.add_mm_to_sizes(event_text_position),
                                     **event.style.get_text_style()))
                    dwg.add(grp)

            date_rect_pos = (centering_offset_x, date_rect_pos[1] + date_rect_size[1])

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
            elif file_format == "pdf":
                svg = dwg.draw_to_buffer()
                cairosvg.svg2pdf(svg.getvalue(), write_to=filename)
                svg.close()

        return

if __name__ == "__main__":
    FILE_NAME = "test.svg"
    PDF_FILE_NAME = FILE_NAME + ".pdf"

    normal_date = PlannerEventStyle()
    vacante = PlannerEventStyle(background_color=(208, 255, 156))
    zile_libere = PlannerEventStyle(background_color=(255, 0, 0))
    weekend = PlannerEventStyle(background_color=(244, 44, 440))

    events = [PlannerEvent((datetime.date(2015, 8, 15), datetime.date(2015, 8, 24)),
                           name="Test Event 1",
                           style=PlannerEventStyle(background_color=(255, 255, 89)),
                           event_type="normal"),
              PlannerEvent((datetime.date(2015, 3, 15), datetime.date(2015, 5, 15)),
                           name="Test Event 2",
                           style=PlannerEventStyle(background_color=(240, 37, 89)),
                           event_type="normal"),
              PlannerEvent((datetime.date(2015, 3, 18), datetime.date(2015, 4, 20)),
                           name="Test Event 3",
                           style=PlannerEventStyle(background_color=(37, 89, 240)),
                           event_type="normal"),
              PlannerEvent((datetime.date(2015, 2, 18), datetime.date(2015, 3, 20)),
                           name="Test Event 4",
                           style=PlannerEventStyle(background_color=(37, 89, 240)),
                           event_type="normal"),
              PlannerEvent((datetime.date(2015, 3, 22), datetime.date(2015, 3, 25)),
                           name="Test Event 5",
                           style=PlannerEventStyle(background_color=(255, 255, 89)),
                           event_type="normal"),
              PlannerEvent((datetime.date(2015, 2, 2), datetime.date(2015, 2, 6)),
                           name="Vacanta #1",
                           event_type="background"),
              PlannerEvent((datetime.date(2015, 6, 15), datetime.date(2015, 8, 31)),
                           name="Vacanta #2",
                           event_type="background"),
              PlannerEvent(datetime.date(2015, 6, 1),
                           name="Rusalii",
                           event_type="background",
                           style=zile_libere)]

    planner = PlannerRenderer(events=events)
    planner.get_planner(output_format="file", filename=PDF_FILE_NAME, file_format="pdf")