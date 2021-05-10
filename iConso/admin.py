from django.contrib import admin
from django.contrib.auth import get_user_model
from django import forms
from django.contrib.auth.admin import UserAdmin
from .forms import SignUpForm
from .models import *
from import_export.admin import ImportExportModelAdmin 
from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.urls import reverse

admin.site.site_title = 'iConso'
admin.site.site_header = 'iConso Administration'
# admin.site.register(Company_Master)
admin.site.register(Periods)
# admin.site.register(COA_Master)
# admin.site.register(FS_grouping_Master)
# admin.site.register(Trial_balance)
# admin.site.register(Interco_transactions)
admin.site.register(Journals)
admin.site.register(JournalHeader)


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'
    readonly_fields = ('action_time',)
    list_filter = ['user', 'content_type']
    search_fields = ['user','object_repr', 'change_message']
    list_display = ['__str__', 'content_type', 'action_time', 'user', 'object_link']

    # keep only view permission
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = obj.object_repr
        else:
            ct = obj.content_type
            try:
                link = mark_safe('<a href="%s">%s</a>' % (
                                 reverse('admin:%s_%s_change' % (ct.app_label, ct.model),
                                         args=[obj.object_id]),
                                 escape(obj.object_repr),
                ))
            except NoReverseMatch:
                link = obj.object_repr
        return link
    object_link.admin_order_field = 'object_repr'
    object_link.short_description = 'object'

    def queryset(self, request):
        return super(LogEntryAdmin, self).queryset(request).prefetch_related('content_type')

def group(self, user):
    groups = []
    for group in user.groups.all():
        groups.append(group.name)
    return ' '.join(groups)
group.short_description = 'Groups'

list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'group')

class MyUserAdmin(UserAdmin):
    add_form = SignUpForm
    # form = MyUserChangeForm
    model = MyUserModel    
    list_display = ['username','email','first_name','last_name','company_code','is_active','is_staff','is_superuser','last_login']
    fieldsets = (
        (None, {'fields': ('username','email','first_name','last_name','company_code','is_active' , 'is_staff', 'is_superuser', 'password')}),
        # ('Personal info', {'fields': ('first_name','last_name','company_code')}),
        ('Groups', {'fields': ('groups',)}),
        ('Permissions', {'fields': ('user_permissions',)}),
        ('Important dates', {'fields': ('last_login','date_joined')}),
    )
    add_fieldsets = (
        (None, {'fields': ('username','email','first_name','last_name','company_code','is_active' , 'is_staff', 'is_superuser', 'password1', 'password2')}),
        # ('Personal info', {'fields': ('first_name','last_name','company_code')}),
        ('Groups', {'fields': ('groups',)}),
        ('Permissions', {'fields': ('user_permissions',)}),
        ('Important dates', {'fields': ('last_login','date_joined')}),
    )
    
    search_fields = ('email', 'first_name','company_code')
    ordering = ('email',)
    filter_horizontal = ()
    #this will allow to change these fields in admin module
admin.site.register(MyUserModel, MyUserAdmin)

@admin.register(Trial_balance)
class Tb_admin(admin.ModelAdmin):
    list_display = ('id','company_code','period_code','account_code','tb_amount' ,'tb_file_name')

@admin.register(Interco_transactions)
class interco_admin(admin.ModelAdmin):
    list_display = ('id' , 'company_code', 'period_code' ,  'rpt_interco_code' ,'account_code' , 'rpt_amount', 'rpt_file_name')

@admin.register(Company_Master)
class company_admin(admin.ModelAdmin):
    list_display = ('id' , 'company_code', 'company_name' ,  'company_type' ,'parent_company' , 'company_start_date', 'company_end_date')

@admin.register(Plan_Master)
class plan_admin(admin.ModelAdmin):
    list_display = ('id' , 'plan_code', 'plan_description' ,  'plan_price' ,'plan_date_create' , 'plan_date_update')

@admin.register(Subscription_Master)
class subscription_admin(admin.ModelAdmin):
    list_display = ('id' , 'company_code', 'plan_code' ,  'start_date' ,'end_date' , 'date_create', 'date_update')

@admin.register(COA_Master)
class coa_master_admin(admin.ModelAdmin):
    list_display = ('id' , 'company_code', 'account_code' ,  'account_name' ,'fs_group' , 'wk_group_row', 'account_date_create', 'account_date_update')


@admin.register(FS_grouping_Master)
class FSgrouping_admin(admin.ModelAdmin):
    list_display = ('id' , 'company_code', 'fs_group_row' ,  'fs_group_name' ,'wk_group_row' , 'wk_group_name', 'account_type', 'account_subtype','fs_date_create','fs_date_update')