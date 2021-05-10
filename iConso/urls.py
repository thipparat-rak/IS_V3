from django.contrib import admin
from django.conf.urls import url
from django.urls import path, re_path
from iConso import views
from .views import SignUpView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    # path('admin/', admin.site.urls),
    path('', views.Home, name='Home'),
    path('Home', views.Home),
    path('Register', views.SignUpView , name='Register'),
    path('Login', views.SignInView, name='Login'),
    path('Logout', views.SignOutView, name='Logout'),
    path('ChangePassword', views.ChangePassword, name='ChangePassword'),

    # url(r'^password/$', views.ChangePassword, name='ChangePassword'),
    # url(r'profile/(?P<username>[a-zA-Z0-9]+)$', views.UserProfile ,name='UserProfile'),
    path('UserProfile', views.UserProfile, name='UserProfile'),
    path('ImportFsGrouping', views.ImportFsGrouping, name='ImportFsGrouping'),
    path('ImportCOA', views.ImportCOA, name='ImportCOA'),
 
    path('RptResult', views.RptResult,name='RptResult'),

    path('Working_bs', views.Working_bs,name='Working_bs'),
    path('Working_pl', views.Working_pl,name='Working_pl'),
    path('Report_bs', views.Report_bs,name='Report_bs'),
    path('Report_pl', views.Report_pl,name='Report_pl'),

    path('CompanySummary', views.CompanySummary, name='CompanySummary'),
    path('CompanyCreate', views.CompanyCreate, name='CompanyCreate'),
    path('CompanyCreate_parent', views.CompanyCreate_parent, name='CompanyCreate_parent'),
    path('company/update/<int:id>/', views.CompanyUpdate, name='CompanyUpdate'),
    path('company/delete/<int:id>/', views.CompanyDelete, name='CompanyDelete'),

    path('PeriodsSummary', views.PeriodsSummary, name='PeriodsSummary'),
    path('PeriodsCreate', views.PeriodsCreate,  name='PeriodsCreate'),
    path('periods/update/<int:id>/', views.PeriodsUpdate, name='PeriodsUpdate'),
    path('periods/delete/<int:id>/', views.PeriodsDelete, name='PeriodsDelete'),

    path('CoaMasterSummary', views.CoaMasterSummary, name='CoaMasterSummary'),
    path('CoaMasterCreate', views.CoaMasterCreate, name='CoaMasterCreate'),
    path('CoaMaster/update/<int:id>/', views.CoaMasterUpdate, name='CoaMasterUpdate'),
    path('CoaMaster/delete/<int:id>/', views.CoaMasterDelete, name='CoaMasterDelete'),

    path('FsGroupingSummary', views.FsGroupingSummary, name='FsGroupingSummary'),
    path('FsGroupingCreate', views.FsGroupingCreate, name='FsGroupingCreate'),
    path('FsGrouping/update/<int:id>/', views.FsGroupingUpdate, name='FsGroupingUpdate'),
    path('FsGrouping/delete/<int:id>/', views.FsGroupingDelete, name='FsGroupingDelete'),

    path('MemberCreate', views.MemberCreate, name='MemberCreate'),
    path('MemberSummary', views.MemberSummary, name='MemberSummary'),
    path('Member/delete/<int:id>/', views.MemberDelete, name='MemberDelete'),

    path('ImportTB', views.ImportTB, name='ImportTB'),
    path('ImportTB/delete/<str:id>/', views.TBDelete, name='TBDelete'),

    path('ImportRPT', views.ImportRPT, name='ImportRPT'),
    path('ImportRPT/delete/<str:id>/', views.RPTDelete, name='RPTDelete'),

    path('ReclassCreateHeader', views.ReclassCreateHeader, name='ReclassCreateHeader'),
    path('ReclassSummary', views.ReclassSummary, name='ReclassSummary'),
    path('ReclassCreate', views.ReclassCreate, name='ReclassCreate'),
    path('Reclass/view/<int:id>/', views.ReclassDetail, name='ReclassDetail'),
    path('Reclass/update/<int:id>/', views.ReclassUpdate, name='ReclassUpdate'),
    path('Reclass/delete/<int:id>/', views.ReclassHeaderDelete, name='ReclassHeaderDelete'),

    path('TakeEqCreateHeader', views.TakeEqCreateHeader, name='TakeEqCreateHeader'),
    path('TakeEqSummary', views.TakeEqSummary, name='TakeEqSummary'),
    path('TakeEqCreate', views.TakeEqCreate, name='TakeEqCreate'),
    path('TakeEq/view/<int:id>/', views.TakeEqDetail, name='TakeEqDetail'),
    path('TakeEq/update/<int:id>/', views.TakeEqUpdate, name='TakeEqUpdate'),
    path('TakeEq/delete/<int:id>/', views.TakeEqHeaderDelete, name='TakeEqHeaderDelete'),

    path('SubscriptionReport', views.SubscriptionReport, name='SubscriptionReport'),
    path('CompanyMemberReport', views.CompanyMemberReport, name='CompanyMemberReport'),
    path('PlanPriceReport', views.PlanPriceReport, name='PlanPriceReport'),
    path('UserReport', views.UserReport, name='UserReport'),
    path('AdminLogReport', views.AdminLogReport, name='AdminLogReport'),

    # url(r'^export/xlsx/$', views.Report_pl, name='Report_pl'),

]


urlpatterns += static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)