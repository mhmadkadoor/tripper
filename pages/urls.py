from django.contrib import admin
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create_trip/', views.create_trip, name='create_trip'),
    path('trip/<int:trip_id>/delete/', views.delete_trip, name='delete_trip'),
    path('trip/<int:trip_id>/', views.trip_details, name='trip_details'),
    path('join-trip/', views.join_trip, name='join_trip'),
    path('item/<int:item_id>/pay/', views.pay_item, name='pay_item'),
    path('trip/<int:trip_id>/add-item/', views.add_item, name='add_item'),
    path('trip/<str:trip_code>/join/', views.join_trip_by_code, name='join_trip_by_code'),
    path('trip/<int:trip_id>/leave/', views.leave_trip, name='leave_trip'),
    path('get_trip_info/<str:trip_code>/', views.get_trip_info, name='get_trip_info'),
    path('trip/<int:trip_id>/confirm-payment/', views.confirm_payment, name='confirm_payment'),
    path('trip/<int:trip_id>/end/', views.end_trip, name='end_trip'),
    path('trip/delete/<int:item_id>/', views.delete_item, name='delete_item' ),
    path('user/get-user-iban/<int:user_id>/', views.get_user_iban, name='get_user_iban'),
    path('user/set-profile/', views.set_profile, name='set_profile')

]
