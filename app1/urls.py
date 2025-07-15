from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.firstpage, name='landing'),
    path('home/', views.home, name='home'),
    path('signin/',views.sign_in,name='signin'), #
    path('signup/', views.signup, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    path('chattoai/', views.chattoai, name='chattoai'),
    path('chattopdf/', views.chattopdf, name='chattopdf'),
    path('builtownai/', views.builtownai, name='builtownai'),
    path('aboutus/', views.aboutus,name="aboutus"),
    path('setting/', views.setting,name="setting"),
    path('aboutinfo/', views.aboutinfo,name="aboutinfo"),
    # path('home/', views.home, name='home'),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:  # Only serve media files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
