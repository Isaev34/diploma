from django.urls import path

from .views import ShiftEndView, ShiftHistoryView, ShiftStartView, ShiftStatsView, SupportInfoView


urlpatterns = [
    path("start/", ShiftStartView.as_view(), name="shift-start"),
    path("end/", ShiftEndView.as_view(), name="shift-end"),
    path("stats/", ShiftStatsView.as_view(), name="shift-stats"),
    path("history/", ShiftHistoryView.as_view(), name="shift-history"),
    path("support/", SupportInfoView.as_view(), name="support-info"),
]

