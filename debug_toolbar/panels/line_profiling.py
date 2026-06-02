import inspect
from io import StringIO

from debug_toolbar.panels import Panel
from django.urls import resolve
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import View
from line_profiler import LineProfiler, show_func

class LineProfilingPanel(Panel):
    is_async = False
    title = _("Line Profiling")
    template = "debug_toolbar/panels/line_profiling.html"

    def _unwrap_closure_and_profile(self, func):
        if not hasattr(func, "__code__") or func in self._added:
            return
        self._added.add(func)
        self.line_profiler.add_function(func)
        for subfunc in getattr(func, "profile_additional", []):
            self._unwrap_closure_and_profile(subfunc)
        if func.__closure__:
            for cell in func.__closure__:
                try:
                    target = cell.cell_contents
                except ValueError:
                    continue
                if hasattr(target, "__code__"):
                    self._unwrap_closure_and_profile(target)
                if inspect.isclass(target) and View in inspect.getmro(target):
                    for name, value in inspect.getmembers(target):
                        if not name.startswith("__") and (
                            inspect.ismethod(value) or inspect.isfunction(value)
                        ):
                            self._unwrap_closure_and_profile(value)

    def process_request(self, request):
        view_func, _, _ = resolve(request.path)
        self.line_profiler = LineProfiler()
        self._added = set()
        self._unwrap_closure_and_profile(view_func)
        # runcall handles enable/disable internally — no cProfile conflict
        return self.line_profiler.runcall(super().process_request, request)

    def generate_stats(self, request, response):
        if not hasattr(self, "line_profiler"):
            return
        lstats = self.line_profiler.get_stats()
        print(lstats)
        func_list = []
        for (fn, lineno, name), timings in lstats.timings.items():
            out = StringIO()
            try:
                show_func(fn, lineno, name, timings, lstats.unit, stream=out)
                text = out.getvalue()
            except Exception:
                text = ""
            if text:
                func_list.append({"name": f"{name} ({fn}:{lineno})", "text": text})
        self.record_stats({"func_list": func_list})
