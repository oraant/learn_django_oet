"""oet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from pages import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    url(r'^admin/', admin.site.urls),

    url(r'^$', views.overview),
    url(r'^overview/$', views.overview),
    url(r'^architecture/$', views.architecture),
    url(r'^tendency/$', views.tendency),
    url(r'^help/$', views.help),
    url(r'^test/$', views.test),
    url(r'^test2/$', views.test2),
]

urlpatterns += staticfiles_urlpatterns()
