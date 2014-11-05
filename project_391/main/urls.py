from django.conf.urls import patterns, url

from main import views

urlpatterns = patterns(
    '',
    url(r'^$', views.loginPage, name='loginPage'),
    url(r'^login/$', views.loginPage, name='loginPage'),
    url(r'^register/$', views.register, name='register'),
    url(r"^index/$", views.temp_main_page, name='index'),
    url(r"^home/$", views.home_page, name='home'),
    url(r"^upload/$", views.upload, name='upload'),
    url(r"^photo_details/$", views.photo_details, name='photo_details'),
    url(r"^group_management/$", views.group_management, name='group_management'),
    url(r"^remove_user_from_group/$", views.remove_user_from_group, name='remove_user_from_group'),
    url(r"^add_group/$", views.add_group, name='add_group'),
    url(r"^add_user_to_group/$", views.add_user_to_group, name='add_user_to_group'),

)
