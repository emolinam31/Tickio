from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import set_language

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/setlang/", set_language, name="set_language"),
    path("", include("events.urls")),
    path("accounts/", include("accounts.urls", namespace="accounts")),
    path("orders/", include("orders.urls")),
    path("about/", TemplateView.as_view(template_name="about.html"), name="about"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
