from django.conf.urls import url, include
from api.views import course,shoppingcar,payment


urlpatterns = [
    url(r'^coursecategory/$', course.CourseCategoryView.as_view({'get': 'list'})),

    url(r'^course/$', course.CourseView.as_view({'get': 'list'})),
    url(r'^course/(?P<pk>\d+)/$', course.CourseView.as_view({'get': 'retrieve'})),

    url(r'^shoppingcar/$', shoppingcar.ShoppingCarViewSet.as_view()),
    url(r'^payment/$', payment.PaymentViewSet.as_view()),

]




