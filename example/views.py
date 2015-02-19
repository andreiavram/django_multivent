# Create your views here.

from django.http.response import HttpResponse
from django.views.generic.base import View
from multivent.planner_svg import output_svg_planner

__author__ = 'yeti'


class TestPlanner(View):
    FORMATS = ("pdf", "png", "svg")

    def get(self, request, *args, **kwargs):
        response = HttpResponse(content_type="application/svg")


        fmt = request.GET.get("format", "svg")
        if fmt not in TestPlanner.FORMATS:
            fmt = "svg"

        output = output_svg_planner(file_format=fmt)
        response['Content-Disposition'] = 'attachment; filename="planner2015.%s"' % fmt
        response.write(output)
        return response
