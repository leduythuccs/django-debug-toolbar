from debug_toolbar.panels import Panel
from django.utils.translation import gettext_lazy as _


class PyinstrumentPanel(Panel):
    title = _("Pyinstrument")
    template = "debug_toolbar/panels/pyinstrument.html"

    def generate_stats(self, request, response):
        self.record_stats({"profile_active": "profile" in request.GET})
