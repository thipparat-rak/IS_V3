import django_filters
from django_filters import CharFilter
from .models import *

class CoaSerachFilter(django_filters.FilterSet):
    account_code = CharFilter(field_name='account_code', lookup_expr='icontains') 
    account_name = CharFilter(field_name='account_name', lookup_expr='icontains')
    wk_group_row = CharFilter(field_name='wk_group_row', lookup_expr='icontains') 
    class Meta:
        model = COA_Master
        fields = ['company_code','account_code','account_name','wk_group_row']

        
class FsSerachFilter(django_filters.FilterSet):
    wk_group_row = CharFilter(field_name='wk_group_row', lookup_expr='icontains') 
    wk_group_name = CharFilter(field_name='wk_group_name', lookup_expr='icontains')
    fs_group_row = CharFilter(field_name='fs_group_row', lookup_expr='icontains') 
    fs_group_name = CharFilter(field_name='fs_group_name', lookup_expr='icontains')
    account_type = CharFilter(field_name='account_type', lookup_expr='icontains')
    account_subtype = CharFilter(field_name='account_subtype', lookup_expr='icontains')
    class Meta:
        model = FS_grouping_Master
        fields = '__all__'
        exclude = ['company_code','fs_show_status','fs_date_create', 'fs_date_update']

class JournalFilter(django_filters.FilterSet):
    journal_no = CharFilter(field_name='journal_no', lookup_expr='icontains') 
    period_code = CharFilter(field_name='period_code', lookup_expr='icontains')
    company_code = CharFilter(field_name='company_code', lookup_expr='icontains') 
    class Meta:
        model = JournalHeader
        fields = '__all__'
        exclude = ['rpt_interco_code','journal_description', 'journal_date_create','journal_date_update']
