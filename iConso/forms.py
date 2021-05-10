from django import forms
from django.contrib.auth.forms import UserCreationForm, get_user_model
from django.contrib.auth.models import User
from iConso.models import MyUserModel, Company_Master, Periods, COA_Master,FS_grouping_Master, MyUserModel,JournalHeader,Journals
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from crispy_forms.bootstrap import FieldWithButtons,StrictButton
from django.forms.models import inlineformset_factory
from django.forms import formsets,formset_factory,BaseInlineFormSet,BaseFormSet

class SignUpForm(UserCreationForm):
    first_name=forms.CharField(max_length=255,required=True)
    last_name=forms.CharField(max_length=255,required=True)
    class Meta():
        model = MyUserModel
        fields = ('username','email','first_name','last_name','company_code','password1','password2')
        labels = {
            'username': 'Username (Email format)',
        }
        help_texts = {
            'username': 'example@gmail.com',
            'password2': None,
        }
        widgets = {
            'username': forms.EmailInput(),
            # 'email': forms.HiddenInput,
        }

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company_Master
        fields = '__all__'
        excludes = ['company_date_create', 'company_date_update']
        labels = {
            'company_name': 'Company Name',
            'company_code': 'Company Code',
            'company_type': 'Company Type',
            'company_est_date': 'Established date',
            'parent_company' : 'Parent company code',
            'country': 'Country',
            'currency': 'Currency',
            'consolidation_rate': 'Conso Rate',
            'company_start_date': 'Start Date',
            'company_end_date': 'End date',
        }
        TYPE = (('Subsidiary', 'Subsidiary'), ('Associate', 'Associate'),('Investment', 'Investment'))
        widgets = { 
            'company_est_date': forms.DateInput(attrs={'type': 'date'}),
            'company_type': forms.Select(choices=TYPE, attrs={'class': 'form-control'}),
            'consolidation_rate': forms.NumberInput(),
            'company_start_date': forms.DateInput(attrs={'type': 'date'}),
            'company_end_date': forms.DateInput(attrs={'type': 'date'}),
            'parent_company': forms.HiddenInput,
        }

class PeriodsForm(forms.ModelForm):
    class Meta:
        model = Periods
        fields = '__all__'
        excludes = ['period_update', 'period_create','company_code']
        ordering = ['period_code']
        labels = {
            'company_code': 'Company Code',
            'period_code': 'Period Code',
            'period_description': 'Period Name',
            'period_date_from': 'Start Date',
            'period_date_to': 'End Date',
            'period_status': 'Status',
            # 'period_create': 'Create Date',
            # 'period_update': 'Update Date',
        }
        widgets = {
            'period_date_from': forms.DateInput(attrs={'type': 'date'}),
            'period_date_to': forms.DateInput(attrs={'type': 'date'}),
            'period_status': forms.Select(),
            'company_code': forms.HiddenInput,
        }

class PeriodsSearchForm(forms.Form):
    PeriodsSearch = forms.CharField(widget = forms.TextInput())

class CoaMasterForm(forms.ModelForm):
    company_code = forms.ModelChoiceField(queryset = Company_Master.objects.all())
    # wk_group_row = forms.ModelChoiceField(queryset = FS_grouping_Master.objects.all())
    class Meta:
        model = COA_Master
        fields = '__all__'
        excludes = ['account_date_create', 'account_date_update']
        labels = {
            'company_code': 'Company Code',
            'account_code': 'Account Code',
            'account_name': 'Account Name',
            'account_type': 'Account Type',
            'fs_group': 'Working Group Row',
            'fs_group_code': 'FS Group Code',
            'fs_group_name': 'FS Group Name',
            'wk_group_row': 'Working Group Row',
            'wk_group_name': 'Working Group Name',
        }
        widgets = {
            'company_code': forms.HiddenInput,
            'fs_group_code': forms.HiddenInput,
            'fs_group_name': forms.HiddenInput,
            'account_type': forms.HiddenInput,
        }
    def __init__(self, *args, **kwargs):
       user_com_code = kwargs.pop('user_company_code', None)
       super(CoaMasterForm, self).__init__(*args, **kwargs)
       if user_com_code:
            self.fields['company_code'].queryset = Company_Master.objects.filter(parent_company = user_com_code)
            self.fields['fs_group'].queryset = FS_grouping_Master.objects.filter(company_code = user_com_code)

class FsGroupingForm(forms.ModelForm):
    # company_code = forms.ModelChoiceField(queryset = Company_Master.objects.all())
    class Meta:
        model = FS_grouping_Master
        fields = '__all__'
        excludes = ['fs_date_create', 'fs_date_update']
        labels = {
            'company_code': 'Company Code',
            'fs_group_row': 'FS Group Row',
            'fs_group_name': 'FS Group Name',
            'wk_group_row': 'Working Group Row',
            'wk_group_name': 'Working Group Name',
            'account_type': 'Account Type',
            'account_subtype': 'Account sub-type',
            # 'fs_parent_group_code': 'FS Parent Group Code',
            # 'fs_level': 'FS Level',
            'fs_show_status': 'Show report',
        }
        widgets = {
            'account_type': forms.Select(),
            'account_subtype': forms.Select(),
            # 'fs_level': forms.Select(),
            'fs_show_status': forms.Select(),
            'company_code': forms.HiddenInput,
        }
    
class MemberForm(UserCreationForm):
    first_name=forms.CharField(max_length=255,required=True)
    last_name=forms.CharField(max_length=255,required=True)
    class Meta():
        model = MyUserModel
        fields = ('username','email','first_name','last_name','company_code','password1','password2')
        labels = {
            'username': 'Username (Email format)',
        }
        help_texts = {
            'username': 'example@gmail.com',
            'password2': None,
        }
        widgets = {
            'username': forms.EmailInput(),
            # 'email': forms.HiddenInput,
        }

class UploadTBForm(forms.Form):
    TBforms = forms.FileField(label='TB Upload :  ',)

class UploadRPTForm(forms.Form):
    RPTforms = forms.FileField(label='RPT Upload :  ',)

class UploadFsGroupingForm(forms.Form):
    FsGroupingforms = forms.FileField(label='FS Grouping Upload :  ',)

class UploadCOAForm(forms.Form):
    COAforms = forms.FileField(label='COA Upload :  ',)

class InterCoForm(forms.Form):
    PeriodsFilter = forms.CharField(required=True, label="Periods Filter")
    # CompanyFilter = forms.CharField(required=True, label="Company Filter")
    
class ReclassHeaderForm(forms.ModelForm):
    period_code = forms.ModelChoiceField(queryset=Periods.objects.all())
    company_code = forms.ModelChoiceField(queryset=Company_Master.objects.all())
    # period_code = forms.ModelChoiceField(queryset=Periods.objects.filter(period_status='Open').filter(company_code = Parent_company_code))
    class Meta:
        model = JournalHeader
        fields = '__all__'
        excludes = ['journal_date_create', 'journal_date_update', 'journal_no','sum_amount','journal_type']
        labels = {
            'period_code': 'Period Code',
            'company_code' : 'Compant Code',
            'Parent_company_code': 'Parent company code',
            'journal_description': 'Journal description',
        }
        widgets = {
            'journal_type': forms.HiddenInput,
        }
    def __init__(self, *args, **kwargs):
       user_com_code = kwargs.pop('user_company_code', None)
       super(ReclassHeaderForm, self).__init__(*args, **kwargs)
       if user_com_code:
            self.fields['period_code'].queryset = Periods.objects.filter(period_status='Open', company_code = user_com_code)
            self.fields['company_code'].queryset = Company_Master.objects.filter(parent_company = user_com_code)

class ReclassForm(forms.ModelForm):
    account_code = forms.ModelChoiceField(queryset = COA_Master.objects.all())
    account_name = forms.ModelChoiceField(queryset=COA_Master.objects.all(), to_field_name='account_name', required=False)
    # account_name = forms.ModelChoiceField(queryset=COA_Master.objects.filter(account_code=account_code).values_list('account_name', flat=True))
    debit = forms.FloatField(required=False ,min_value=0)
    credit = forms.FloatField(required=False ,min_value=0)
    class Meta:
        model = Journals
        fields = '__all__'
        excludes = ['journal_date_create', 'journal_date_update']
        labels = {
            'journal_no': 'Journal no.',
            'company_code': 'Company Code',
            'account_code': 'Account code',
            'account_name': 'Account Name',
            'debit': 'debit',
            'credit': 'credit',
        }
        widgets = {
            'journal_no': forms.HiddenInput,
            'journal_indicator': forms.HiddenInput,
            'journal_amount': forms.HiddenInput,
            'JournalHeader': forms.HiddenInput,
        }
    def __init__(self, *args, **kwargs):
        user_com_code = kwargs.pop('user_company_code', None)
        super(ReclassForm, self).__init__(*args, **kwargs)
        if user_com_code:
            self.fields['account_code'].queryset = COA_Master.objects.filter(company_code = user_com_code)
            self.fields['account_name'].queryset = COA_Master.objects.filter(company_code = user_com_code).values_list('account_name', flat=True)
            
ReclassFormset = inlineformset_factory(JournalHeader, Journals, form=ReclassForm, extra=10 ,can_delete=True)

class WorkingForm(forms.Form):
    PeriodsFilter = forms.CharField(required=True, label="Periods Filter")
    # ParentCompanyFilter = forms.CharField(required=True, label="Parent Company Filter")

class TakeEqHeaderForm(forms.ModelForm):
    period_code = forms.ModelChoiceField(queryset=Periods.objects.all())
    company_code = forms.ModelChoiceField(queryset=Company_Master.objects.all())
    # period_code = forms.ModelChoiceField(queryset=Periods.objects.filter(period_status='Open').filter(company_code = Parent_company_code))
    class Meta:
        model = JournalHeader
        fields = '__all__'
        excludes = ['journal_date_create', 'journal_date_update', 'journal_no','sum_amount','journal_type']
        labels = {
            'period_code': 'Period Code',
            'company_code' : 'Compant Code',
            'Parent_company_code': 'Parent company code',
            'journal_description': 'Journal description',
        }
        widgets = {
            'journal_type': forms.HiddenInput,
        }
    def __init__(self, *args, **kwargs):
       user_com_code = kwargs.pop('user_company_code', None)
       super(TakeEqHeaderForm, self).__init__(*args, **kwargs)
       if user_com_code:
            self.fields['period_code'].queryset = Periods.objects.filter(period_status='Open', company_code = user_com_code)
            self.fields['company_code'].queryset = Company_Master.objects.filter(parent_company = user_com_code)

class TakeEqForm(forms.ModelForm):
    account_code = forms.ModelChoiceField(queryset = COA_Master.objects.all())
    account_name = forms.ModelChoiceField(queryset=COA_Master.objects.all(), to_field_name='account_name', required=False)
    # account_name = forms.ModelChoiceField(queryset=COA_Master.objects.filter(account_code=account_code).values_list('account_name', flat=True))
    debit = forms.FloatField(required=False ,min_value=0)
    credit = forms.FloatField(required=False ,min_value=0)
    rpt_interco_code = forms.ModelChoiceField(queryset=Company_Master.objects.all())
    class Meta:
        model = Journals
        fields = '__all__'
        excludes = ['journal_date_create', 'journal_date_update']
        labels = {
            'journal_no': 'Journal no.',
            'company_code': 'Company Code',
            'account_code': 'Account Code',
            'account_name': 'Account Name',
            'rpt_interco_code': 'Intercompany Code',
            'debit': 'Debit',
            'credit': 'Credit',
        }
        widgets = {
            'journal_no': forms.HiddenInput,
            'journal_indicator': forms.HiddenInput,
            'journal_amount': forms.HiddenInput,
            'JournalHeader': forms.HiddenInput,
        }
    def __init__(self, *args, **kwargs):
        user_com_code = kwargs.pop('user_company_code', None)
        super(TakeEqForm, self).__init__(*args, **kwargs)
        if user_com_code:
            self.fields['account_code'].queryset = COA_Master.objects.filter(company_code = user_com_code)
            self.fields['account_name'].queryset = COA_Master.objects.filter(company_code = user_com_code).values_list('account_name', flat=True)
            self.fields['rpt_interco_code'].queryset = Company_Master.objects.filter(parent_company = user_com_code)

TakeEqFormset = inlineformset_factory(JournalHeader, Journals, form=TakeEqForm, extra=10 ,can_delete=True)

class SubscriptionForm(forms.Form):
    CompanyCodeFilter = forms.CharField(label="Company Code Filter",required=False)
    CompanyNameFilter = forms.CharField(label="Company Name Filter",required=False)
    PlanCodeFilter = forms.CharField(label="Plan Code Filter",required=False)

class CompanyMemberForm(forms.Form):
    CompanyCodeFilter = forms.CharField(label="Company Code Filter",required=False)
    CompanyNameFilter = forms.CharField(label="Company Name Filter",required=False)
    ParentCompanyFilter = forms.CharField(label="Parent Company Code Filter",required=False)

class UserAdminForm(forms.Form):
    UsernameFilter = forms.CharField(label="Username Filter",required=False)
    FirstNameFilter = forms.CharField(label="First Name Filter",required=False)
    LastNameFilter = forms.CharField(label="Last Name Filter",required=False)
    CompanyCodeFilter = forms.CharField(label="Company Code Filter",required=False)

class AdminLogForm(forms.Form):
    UsernameFilter = forms.CharField(label="Username Filter",required=False)
    DateFilter = forms.DateField(label="Date Filter",required=False)