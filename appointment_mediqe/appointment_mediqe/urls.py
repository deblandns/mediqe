from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from . import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/accounts/", include("accounts.v1.urls")),
]

# add static file serving just for debug True
if settings.DEBUG:
    urlpatterns = urlpatterns + static(
        settings.STATIC_URL, document_root=settings.STATIC_ROOT
    )
