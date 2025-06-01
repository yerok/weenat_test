"""
URL configuration for weenat_test_api project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from api.views import IngestDataView, FetchRawDataView, SummaryView



# Django can't use a class so we transform the class as a function
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/ingest/', IngestDataView.as_view(), name="api_ingest_data" ),
    path('api/data/', FetchRawDataView.as_view(), name="api_fetch_data_raw" ),
    path('api/summary/', SummaryView.as_view(), name="api_fetch_data_aggregates" )
]
