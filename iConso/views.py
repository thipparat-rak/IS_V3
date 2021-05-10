from django.shortcuts import render, redirect, HttpResponse
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate,logout,update_session_auth_hash
from django.contrib.auth.models import Group, User, Permission, AbstractBaseUser,AbstractUser,BaseUserManager,PermissionsMixin
from django.db.models.signals import post_save
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse,reverse_lazy
from django.db.models import Q, Count, Sum, Max, Min
from django.views.decorators.csrf import csrf_exempt
from django.template import loader,RequestContext
from .filters import CoaSerachFilter,FsSerachFilter,JournalFilter
from .forms import *
from django.forms import inlineformset_factory
from .resources import TrialResources , IntercoResources
from .models import *
from django.views.generic.edit import CreateView,FormView, UpdateView
from django_pandas.io import read_frame
from io import BytesIO
import pandas as pd
import numpy as np
from datetime import datetime
from django.db.models.functions import TruncMinute
from django.db import transaction
from django.contrib.admin.models import LogEntry, DELETION
from django.contrib.contenttypes.models import ContentType

def is_manager(user):
    return user.groups.filter(name='Manager').exists()
def is_in_user_groups(user):
    return user.groups.filter(name__in=['Accountant', 'Manager']).exists()
def is_in_all_groups(user):
    return user.groups.filter(name__in=['Accountant', 'Manager', 'Viewer']).exists()

@login_required(login_url='Login')
def Home(request):
    user_com_code = request.user.company_code
    CurrentPeriod = Periods.objects.all().filter(period_status = 'Open',company_code= user_com_code)
    return render(request,'Home.html', {'CurrentPeriod': CurrentPeriod})

############### User ###############
def SignUpView(request):
    if request.method in ('POST', 'PUT'):
        data = request.POST.copy()
        data['email'] = request.POST.get('username', "")
        form = SignUpForm(data)
        # form = SignUpForm(request.POST)
        if form.is_valid():
            #บันทึกข้อมูล User
            r =  form.save()
            #บันทึก Group Customer
            username = form.cleaned_data.get('username') #ดึง username จากแบบฟอร์มมาใช้
            SignUpUser = MyUserModel.objects.get(username=username) #ดึงข้อมูล user จากฐานข้อมูล
            member_group = Group.objects.get(name="Manager") #ดึงคำว่า Manager มาจาก Group
            member_group.user_set.add(SignUpUser) #Set ค่า group ให้ User

            # #โดยเก็บข้อมูลบางอย่างไว้ในเซสชัน
            request.session['id'] = r.id  
            request.session['first_name'] = r.first_name    
            request.session['last_name'] =  r.last_name 

            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect(reverse('Home'))
    else:
        form = SignUpForm()
    return render(request, 'Register.html', {'form': form})

def SignInView(request):
    if request.method=='POST':
        form=AuthenticationForm(data=request.POST)
        if form.is_valid():
            username=request.POST['username']
            password=request.POST['password']
            user = authenticate(username=username,password=password)
            
            if user is not None :
                login(request,user)
                # request.session['User'] = user
                return redirect('Home')
            else :
                return redirect('Register')
    else:
        form=AuthenticationForm()
    return render(request,'Login.html',{'form':form})

def SignOutView(request):
    logout(request)
    return redirect('Login')

@login_required(login_url='Login')
def ChangePassword(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Important!
            messages.success(request, 'Your password was successfully updated!')
            return redirect('ChangePassword')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'ChangePassword.html', {
        'form': form
    })

@login_required(login_url='Login')
def UserProfile(request):
    user_com_code = request.user.company_code
    company_list = Company_Master.objects.filter(company_code=user_com_code)
    return render(request, 'UserProfile.html', {'company_list': company_list,  } )

############### Member ###############
@login_required(login_url='Login')
def MemberSummary(request):
    user_com_code = request.user.company_code
    company_list = Company_Master.objects.filter(parent_company=user_com_code)
    data = MyUserModel.objects.filter(company_code__in = company_list)
    return render(request, 'MemberSummary.html', {'data': data,  })

@login_required(login_url='Login')
def MemberCreate(request):
    # if request.method == 'POST':
    if 'Accountant' :
        if request.method in ('POST', 'PUT'):
             #กดปุ่ม Save as Accountant
            data = request.POST.copy()
            data['email'] = request.POST.get('username', "")
            form = SignUpForm(data)
            # form = MemberForm(request.POST)
            if form.is_valid():
                #บันทึกข้อมูล User
                r = form.save()
                #บันทึก Group Customer
                username = form.cleaned_data.get('username') #ดึง username จากแบบฟอร์มมาใช้
                SignUpUser = MyUserModel.objects.get(username=username) #ดึงข้อมูล user จากฐานข้อมูล
                member_group = Group.objects.get(name="Accountant") #ดึงคำว่า Member มาจาก Group
                member_group.user_set.add(SignUpUser) #Set ค่า group ให้ User
                #โดยเก็บข้อมูลบางอย่างไว้ในเซสชัน
                messages.success(request, 'Your member was create successfully!')
                return redirect(reverse('MemberSummary'))
    elif 'Viewer' in request.POST: #กดปุ่ม Save as Viewer
        data = request.POST.copy()
        data['email'] = request.POST.get('username', "")
        form = SignUpForm(data)
        # form = SignUpForm(request.POST)
        if form.is_valid():
            #บันทึกข้อมูล User
            r = form.save()
            #บันทึก Group Customer
            username = form.cleaned_data.get('username') #ดึง username จากแบบฟอร์มมาใช้
            SignUpUser = MyUserModel.objects.get(username=username) #ดึงข้อมูล user จากฐานข้อมูล
            member_group = Group.objects.get(name="Viewer") #ดึงคำว่า Member มาจาก Group
            member_group.user_set.add(SignUpUser) #Set ค่า group ให้ User
            #โดยเก็บข้อมูลบางอย่างไว้ในเซสชัน
            return redirect(reverse('MemberSummary'))
    else:
        form = SignUpForm()

    return render(request, 'MemberCreate.html', {
        'form': form,
    })

@login_required(login_url='Login')
def MemberDelete(request, id):
    User.objects.get(id=id).delete()
    data = User.objects.filter()[:10]
    return render(request, 'MemberSummary.html', {'data': data})

############### Company ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CompanySummary(request):
    user_com_code = request.user.company_code
    data = Company_Master.objects.filter(parent_company=user_com_code)
    return render(request, 'CompanySummary.html', {'data': data})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CompanyCreate(request):
    user_com_code = request.user.company_code
    group = request.user.groups.all
    print(group)
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.parent_company = str(user_com_code)
            company.save()
            messages.success(request, 'Your company was create successfully!')
            return redirect(reverse('CompanyCreate')) 
    else:
        form = CompanyForm()    
    return render(request, 'CompanyCreate.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CompanyCreate_parent(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your company was create successfully!')
            return redirect(reverse('Register'))
    else:
        form = CompanyForm()    
    return render(request, 'CompanyCreate_parent.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')             
def CompanyUpdate(request, id):
    user_com_code = request.user.company_code
    #ถ้ามีข้อมูลจากฟอร์มถูกส่งเข้ามาด้วยเมธอด POST
    if request.method == 'POST':
        #อ่านข้อมูลเดิม
        row = Company_Master.objects.get(id=id) #get_object_or_404(Employee, id=id)
        #กำหนดข้อมูลเดิมให้กับโมเดลฟอร์ม เพื่อเปรียบเทียบกับข้อมูลใหม่ที่รับเข้ามา
        form = CompanyForm(instance=row, data=request.POST)
        #ถ้าข้อมูลทั้งหมดถูกต้อง
        if form.is_valid():
            #บันทึกการเปลี่ยนแปลงลงในฟิลด์ต่างๆ
            company = form.save(commit=False)
            company.parent_company = str(user_com_code)
            company.save()
            messages.success(request, 'Your Company was updated successfully!')
    else:
        #ถ้าไม่มีข้อมูลส่งจากโมเดลฟอร์มเข้ามา 
        #ให้อ่านข้อมูลเดิม เพื่อนำไปกำหนดเป็นค่าเริ่มแรกของอินพุทแต่ละอัน
        row = Company_Master.objects.get(id=id)
        form = CompanyForm(initial=row.__dict__)
    return render(request, 'CompanyUpdate.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CompanyDelete(request, id):
    user_com_code = request.user.company_code
    Company_Master.objects.get(id=id).delete()
    data = Company_Master.objects.filter(parent_company=user_com_code)[:10]
    return render(request, 'CompanySummary.html', {'data': data})

############### Period ###############
@user_passes_test(is_manager)
@login_required(login_url='Login')
def PeriodsSummary(request):
    user_com_code = request.user.company_code
    data = Periods.objects.filter(company_code=user_com_code).order_by('company_code','-period_date_to')
    return render(request, 'PeriodsSummary.html', {'data': data})

@user_passes_test(is_manager)
@login_required(login_url='Login')
def PeriodsCreate(request):
    user_com_code = request.user.company_code
    # company = Company_Master.objects.all
    if request.method == 'POST':
        form = PeriodsForm(request.POST)
        ComCode = Company_Master.objects.get(company_code=user_com_code).id
        
        if form.is_valid():
            # Period = Periods.objects.create(
            #     company_id = company,
            #     company_code = ComCode,
            #     period_code = period_code,
            #     period_description = period_description,
            #     period_date_from = period_date_from,
            #     period_date_to = period_date_to,
            #     period_status = period_status,
            # )
            # Period.save()
            Period = form.save(commit=False)
            # Period.company_id = ComCode
            try:
                Period.company_code = user_com_code
                Period.save()
                messages.success(request, 'Your period was create successfully!')
            except:
                messages.warning(request ,'Validation! Period already exists')
            return redirect(reverse('PeriodsCreate')) 
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        form = PeriodsForm()
    return render(request, 'PeriodsCreate.html', {'form': form})

    # def save(self, *args, **kwargs):
    #     try:
    #         result = super().save(*args, **kwargs)
    #     except IntegrityError as err:
    #         if str(err) == "Skill group with this User and Skill group already exists.":
    #             raise IntegrityError("Skill Group already in use.")
    #         raise
    #     else:
    #         return result

@user_passes_test(is_manager)
@login_required(login_url='Login')
def PeriodsUpdate(request, id):
    user_com_code = request.user.company_code
    if request.method == 'POST':
        row = Periods.objects.get(id=id) 
        form = PeriodsForm(instance=row, data=request.POST)
        # company = request.POST['company']
        ComCode = Company_Master.objects.get(company_code=user_com_code).id
        period_code = request.POST['period_code']
        period_description = request.POST['period_description']
        period_date_from = request.POST['period_date_from']
        period_date_to = request.POST['period_date_to']
        period_status = request.POST['period_status']
        if form.is_valid():
            try:
                Period = Periods.objects.filter(id=id
                ).update(
                    company_code = str(user_com_code),
                    period_code = period_code,
                    period_description = period_description,
                    period_date_from = period_date_from,
                    period_date_to = period_date_to,
                    period_status = period_status,
                    period_update = datetime.now(),
                )
                messages.success(request, 'Your period was update successfully!')
            except:
                messages.warning(request ,'Validation! Period status invalid')
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        row = Periods.objects.get(id=id)
        form = PeriodsForm(initial=row.__dict__)
    return render(request, 'PeriodsUpdate.html', {'form': form})

@user_passes_test(is_manager)
@login_required(login_url='Login')
def PeriodsDelete(request, id):
    user_com_code = request.user.company_code
    Periods.objects.get(id=id).delete()
    data = Periods.objects.filter(company_code=user_com_code)[:10]
    return render(request, 'PeriodsSummary.html', {'data': data})

@login_required(login_url='Login')
def PeriodsSearch(request):
    user_com_code = request.user.company_code
    if request.method=='POST':
        kw = request.POST.get('PeriodsSearch', '')
        form = PeriodsSearchForm(request.POST, initial={'PeriodsSearch': kw})
    else:
        kw = request.GET.get('PeriodsSearch', '')
        form = PeriodsSearchForm(initial={'PeriodsSearch': kw})
    data = Periods.objects.filter(Q(period_code__contains=kw)&Q(company_code=user_com_code))[:10]
    return render(request, 'PeriodsSummary.html', {'form': form, 'data': data})

############### COA Master ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CoaMasterSummary(request):
    user_com_code = request.user.company_code
    company_list = list(Company_Master.objects.filter(parent_company=user_com_code))
    Coadata = COA_Master.objects.filter(company_code__in = company_list).order_by('company_code','account_code')
    CoaFilter = CoaSerachFilter(request.GET, queryset=Coadata)
    Coadata = CoaFilter.qs
    return render(request, 'CoaMasterSummary.html', {'Coadata': Coadata , 'CoaFilter':CoaFilter})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CoaMasterCreate(request):
    user_com_code = request.user.company_code
    if request.method == 'POST':
        form = CoaMasterForm(request.POST, user_company_code = request.user.company_code)
        wk_group = request.POST['fs_group']
        WkRow = FS_grouping_Master.objects.get(id=wk_group).wk_group_row
        # company = request.POST['company']
        # ComCode = Company_Master.objects.get(id=company).company_code
        if form.is_valid():
            COA = form.save(commit=False)
            COA.wk_group_row = WkRow
            COA.save()
            messages.success(request, 'Your COA was create successfully!')
            return redirect(reverse('CoaMasterCreate')) 
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        form = CoaMasterForm(user_company_code = request.user.company_code)   
    return render(request, 'CoaMasterCreate.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CoaMasterUpdate(request, id):
    user_com_code = request.user.company_code
    if request.method == 'POST':
        row = COA_Master.objects.get(id=id) #get_object_or_404(Employee, id=id)
        #กำหนดข้อมูลเดิมให้กับโมเดลฟอร์ม เพื่อเปรียบเทียบกับข้อมูลใหม่ที่รับเข้ามา
        form = CoaMasterForm(instance=row, data=request.POST,user_company_code = request.user.company_code)
        # wk_group = request.POST['fs_group']
        # WkRow = FS_grouping_Master.objects.get(id=wk_group).wk_group_row
        # company = request.POST['company']
        # ComCode = Company_Master.objects.get(id=company).company_code
        if form.is_valid():
            # COA = form.save(commit=False)
            # COA.company_code = str(user_com_code)
            # COA.wk_group_row = WkRow
            form.save()
            messages.success(request, 'Your COA was updated successfully!')
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        row = COA_Master.objects.get(id=id)
        form = CoaMasterForm(initial=row.__dict__,user_company_code = request.user.company_code)
        # form.fields['company_code'].disabled = True
        # form.fields['fs_group'].disabled = True
    return render(request, 'CoaMasterUpdate.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def CoaMasterDelete(request, id):
    COA_Master.objects.get(id=id).delete()
    return redirect(reverse('CoaMasterSummary')) 

@user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='Login')
def ImportCOA(request):
    if request.method == "POST":
        form = UploadCOAForm(request.POST, request.FILES)
        if form.is_valid():
            COAfile = request.FILES['COAforms']
            df = pd.read_excel(COAfile.temporary_file_path())
            SpecColumn = ['company_code','account_code','account_name','fs_group','wk_group_row']
            df.columns=['company_code','account_code','account_name','fs_group','wk_group_row']
            row_iter = df.iterrows()
            new_COA = [
                COA_Master(
                    company_code = row['company_code'], 
                    account_code = row['account_code'],
                    account_name = row['account_name'], 
                    fs_group_id = row['fs_group'], 
                    wk_group_row = row['wk_group_row'],
                )
                for index, row in row_iter
            ]
            COA_Master.objects.bulk_create(new_COA)
            messages.success(request, 'Your file have been uploaded') 
        return redirect(reverse('ImportCOA'))
    else:
        form = UploadCOAForm()
    return render(request, 'ImportCOA.html', {'form': form,})

############### Fs Grouping ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def FsGroupingSummary(request):
    user_com_code = request.user.company_code
    data = FS_grouping_Master.objects.filter(company_code=user_com_code).order_by('company_code','wk_group_row')
    FsFilter = FsSerachFilter(request.GET, queryset=data)
    data = FsFilter.qs
    return render(request, 'FsGroupingSummary.html', {'data': data, 'FsFilter':FsFilter })

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def FsGroupingCreate(request):
    user_com_code = request.user.company_code
    if request.method == 'POST':
        form = FsGroupingForm(request.POST)
        # company = request.POST['company']
        # ComCode = Company_Master.objects.get(id=company).company_code
        if form.is_valid():
            FsGroup = form.save(commit=False)
            FsGroup.company_code = str(user_com_code)
            FsGroup.save()
            messages.success(request, 'Your FS grouping was create successfully!')
            return redirect(reverse('FsGroupingCreate')) 
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        form = FsGroupingForm()    
    return render(request, 'FsGroupingCreate.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def FsGroupingUpdate(request, id):
    user_com_code = request.user.company_code
    if request.method == 'POST':
        row = FS_grouping_Master.objects.get(id=id) #get_object_or_404(Employee, id=id)
        form = FsGroupingForm(instance=row, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your FS grouping was updated successfully!')
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        row = FS_grouping_Master.objects.get(id=id)
        form = FsGroupingForm(initial=row.__dict__)
    return render(request, 'FsGroupingUpdate.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def FsGroupingDelete(request, id):
    user_com_code = request.user.company_code
    FS_grouping_Master.objects.get(id=id).delete()
    data = FS_grouping_Master.objects.filter(company_code=user_com_code)[:10]
    return render(request, 'FsGroupingSummary.html', {'data': data})

@user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='Login')
def ImportFsGrouping(request):
    if request.method == "POST":
        form = UploadFsGroupingForm(request.POST, request.FILES)
        if form.is_valid():
            FsGroupingfile = request.FILES['FsGroupingforms']
            df = pd.read_excel(FsGroupingfile.temporary_file_path())
            SpecColumn = ['company_code','wk_group_row','wk_group_name','fs_group_row','fs_group_name','account_type','account_subtype']
            df.columns=['company_code','wk_group_row','wk_group_name','fs_group_row','fs_group_name','account_type','account_subtype']
            row_iter = df.iterrows()
            new_FsGrouping = [
                FS_grouping_Master(
                    company_code = row['company_code'], 
                    wk_group_row = row['wk_group_row'],
                    wk_group_name = row['wk_group_name'], 
                    fs_group_row = row['fs_group_row'], 
                    fs_group_name = row['fs_group_name'],
                    account_type = row['account_type'],
                    account_subtype = row['account_subtype'],
                )
                for index, row in row_iter
            ]
            FS_grouping_Master.objects.bulk_create(new_FsGrouping)
            messages.success(request, 'Your file have been uploaded') 
        return redirect(reverse('ImportFsGrouping'))
    else:
        form = UploadFsGroupingForm()
    return render(request, 'ImportFsGrouping.html', {'form': form,})

############### TB ###############
@login_required(login_url='Login')
@user_passes_test(is_in_user_groups)
def ImportTB(request):
    TBsummary = Trial_balance.objects.annotate(date_create=TruncMinute('tb_date_create')).values('company_code','period_code','date_create','tb_file_name').annotate(Sum('tb_amount')).order_by('-date_create')
    CurrentPeriod = Periods.objects.all().filter(period_status = 'Open')
    print(CurrentPeriod)
    if request.method == "POST":
        form = UploadTBForm(request.POST, request.FILES)
        if form.is_valid():
            TBfile = request.FILES['TBforms']
            TBfileName = request.FILES['TBforms'].name
            reTBfileName = TBfileName.translate ({ord(name): "_" for name in "!@#$%^&*'()[]{};:,/<>?\|`~=+"})
            row = Trial_balance.objects.filter(tb_file_name = reTBfileName)
            while (row.count() > 0):
                print('File Duplicate and have been deleted')
                Trial_balance.objects.filter(tb_file_name = reTBfileName).delete()
            print('File Pass')
            try:
                df = pd.read_excel(TBfile.temporary_file_path())            
            except Exception :
                messages.warning(request ,'Invalid File Type!')
                return redirect(reverse('ImportTB'))
            print(TBfile.temporary_file_path())
             #Condition check Column
            SpecColumn = ['company_code','period_code','account_code','account_name','tb_amount']
            if set(SpecColumn) != set(df.columns) :
                messages.warning(request ,'Invalid File Format!')
                return redirect(reverse('ImportTB'))
            df.columns=['company_code','period_code','account_code','account_name','tb_amount']
            #Condition check sum
            check_sum = 0  #กำหนดค่าเริ่มต้นเท่ากัน 0
            for index, row in df.iterrows():        
                check_sum += row['tb_amount']  #เอา field amount เก็บค่าเข้าตัวแปร  check_sum     
            sum_total =  float(format(-check_sum , '.2f'))   #แปลงค่า ให้เป็น float ทศนิยม
            #Read file
            if (sum_total == 0.00): 
                # for index, row in df.iterrows(): 
                #     # print (row["account_code"])
                #     new_Trial_balance = Trial_balance.objects.create(
                #         company_code=row['company_code'], 
                #         period_code=row['period_code'], 
                #         account_code=row['account_code'], 
                #         tb_amount=row['tb_amount'],
                #         tb_file_name=request.FILES['TBforms'].name)
                #     new_Trial_balance.save()
                row_iter = df.iterrows()
                new_TB = [
                    Trial_balance(
                        company_code=row['company_code'], 
                        period_code=row['period_code'], 
                        account_code=row['account_code'], 
                        tb_amount=row['tb_amount'],
                        # tb_file_name=request.FILES['TBforms'].name
                        tb_file_name=reTBfileName
                    )
                    for index, row in row_iter
                ]
                Trial_balance.objects.bulk_create(new_TB)
                messages.success(request, 'Your file have been uploaded') 
            else:  
                messages.warning(request ,'Validation! Sum TB amount not equal to zero 0')
        else:  
            messages.warning(request ,'Validation! ')
        return redirect(reverse('ImportTB'))
    else:
        form = UploadTBForm()
        # new_Trial_balance = Trial_balance.objects.create(company_code='ABC', 
        #     period_code='Q4_2020', account_code='1010', tb_amount='100')
        # new_Trial_balance.save()
    return render(request, 'ImportTB.html', {'TBsummary': TBsummary,'form': form,'CurrentPeriod':CurrentPeriod})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TBDelete(request, id):
    a = Trial_balance.objects.filter(tb_file_name = id)
    print(a)
    Trial_balance.objects.filter(tb_file_name = id).delete()
    return redirect(reverse('ImportTB'))

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def ImportRPT(request):
    RPTfileSummary = Interco_transactions.objects.annotate(date_create=TruncMinute('rpt_date_create')).values('company_code','period_code','date_create','rpt_file_name').annotate(Sum('rpt_amount')).order_by('-date_create')
    if request.method == "POST":
        form = UploadRPTForm(request.POST, request.FILES)
        if form.is_valid():
            RPTfile = request.FILES['RPTforms']
            RPTfileName = request.FILES['RPTforms'].name
            reRPTfileName = RPTfileName.translate ({ord(name): "_" for name in "!@#$%^&*'()[]{};:,/<>?\|`~=+"})
            row = Interco_transactions.objects.filter(rpt_file_name = reRPTfileName)
            # account_code = request.POST['account_code']
            # Company = Company_Master.objects.get(id=company).company_code
            # FsGroup = COA_Master.objects.get(account_code=account_code,company_code=company_code ).fs_group_name
            # print(FsGroup)
            while (row.count() > 0):
                print('File Duplicate and have been deleted')
                Interco_transactions.objects.filter(rpt_file_name = reRPTfileName).delete()
            print('File Pass')
            try:
                df = pd.read_excel(RPTfile.temporary_file_path())            
            except Exception :
                messages.warning(request ,'Invalid File Type!')
                return redirect(reverse('ImportRPT'))
            # print(RPTfile.temporary_file_path())
            # print(df.columns)
            #Condition check Column
            SpecColumn = ['company_code','period_code','rpt_interco_code','account_code','account_name','rpt_amount']
            if set(SpecColumn) != set(df.columns) :
                messages.warning(request ,'Invalid File Format!')
                return redirect(reverse('ImportRPT'))

            df.columns=['company_code','period_code','rpt_interco_code','account_code','account_name','rpt_amount']
            #Condition
            # for index, row in df.iterrows(): 
            #     # print (row["account_code"])
            #     new_RPT = Interco_transactions.objects.create(
            #         company_code=row['company_code'], 
            #         period_code=row['period_code'],
            #         rpt_interco_code=row['rpt_interco_code'], 
            #         account_code=row['account_code'], 
            #         rpt_amount=row['rpt_amount'],
            #         rpt_file_name=request.FILES['RPTforms'].name)
            #     new_RPT.save()
            row_iter = df.iterrows()
            new_RPT = [
                Interco_transactions(
                    company_code = row['company_code'], 
                    period_code = row['period_code'],
                    rpt_interco_code = row['rpt_interco_code'], 
                    account_code = row['account_code'], 
                    rpt_amount = row['rpt_amount'],
                    rpt_file_name = reRPTfileName
                    # rpt_file_name = request.FILES['RPTforms'].name,
                    # fs_group_name = row['FSgroup.fs_group_name'],
                    # account_type = row['FSgroup.account_type']
                )
                for index, row in row_iter
            ]
            Interco_transactions.objects.bulk_create(new_RPT)
            messages.success(request, 'Your file have been uploaded') 
        return redirect(reverse('ImportRPT'))
    else:
        form = UploadRPTForm()
        # new_Trial_balance = Trial_balance.objects.create(company_code='ABC', 
        #     period_code='Q4_2020', account_code='1010', tb_amount='100')
        # new_Trial_balance.save()
    return render(request, 'ImportRPT.html', {'RPTfileSummary': RPTfileSummary,'form': form,})

############### RPT ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def RPTDelete(request, id):
    Interco_transactions.objects.filter(rpt_file_name = id).delete()
    return redirect(reverse('ImportRPT'))

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def RptResult(request):
    user_com_code = request.user.company_code
    final_pivot = ''
    if request.method == "POST":
        form = InterCoForm(request.POST)
        # company = request.POST['CompanyFilter']
        period = request.POST['PeriodsFilter']
        print(period)
        if form.is_valid():
            company_list = Company_Master.objects.filter(parent_company=user_com_code).values('company_code')
            # ComCode = Company_Master.objects.get(id=company).company_code
            qs = Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period))  #ใช้ & เป็นจริงทุกเงื่อนไข ใช้ | เป็นจริงเงื่อนไขใดก็ได้
            if not qs:
                messages.warning(request ,'No data found!')
                return redirect(reverse('RptResult'))
            else:
                pd.options.display.float_format = "{:,.2f}".format
                df_company = pd.DataFrame(list(Company_Master.objects.values('company_code','company_type','parent_company')))
                df_coa = pd.DataFrame(list(COA_Master.objects.filter(company_code__in = company_list).values('company_code','account_code','account_name','wk_group_row')))
                df_fsgroup = pd.DataFrame(list(FS_grouping_Master.objects.filter(company_code = user_com_code).values('company_code','fs_group_row','fs_group_name','wk_group_row','wk_group_name','account_type','account_subtype')))
                
                df_interco = pd.DataFrame(list(Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','rpt_interco_code','account_code','rpt_amount','period_code')))
                df_interco2 = pd.pivot_table(df_interco,values = 'rpt_amount', index=['account_code','period_code', 'rpt_interco_code','company_code'],columns='company_code',aggfunc='sum',fill_value=0,margins=True, margins_name='Total RPT')
                df_interco2.reset_index(inplace=True)
                df_interco3 = df_interco2.iloc[:-1]
                #### result ####
                result = pd.merge(df_interco3, df_company, on=['company_code'], how='left')
                result2 = pd.merge(result, df_coa, on=['account_code','company_code'], how='left')
                result3 = pd.merge(result2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                result4 = result3.drop(columns=['period_code','account_code', 'account_name','fs_group_row','fs_group_name','company_type','company_code_y','company_code_x','parent_company'])
                result4['wk_group_row'] = result4['wk_group_row'].fillna('n/a group')
                result4['wk_group_name'] = result4['wk_group_name'].fillna('n/a group')
                result4['account_type'] = result4['account_type'].fillna('n/a group')
                result4['account_subtype'] = result4['account_subtype'].fillna('n/a group')
                result5 = result4.apply(pd.to_numeric, errors='ignore')
                result6 = result5.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','rpt_interco_code'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                result6.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                result6.loc["Total"] = result6.sum(numeric_only=True, axis=0)
                result6[['wk_group_name']] = result6[['wk_group_name']].fillna(value='Total')
                result6.fillna('',inplace=True)
                Colname = {'rpt_amount':'RPT amount','account_type':'Account type', 'account_subtype':'Account subtype', 'wk_group_row':'WK group row','wk_group_name':'WK group name','rpt_interco_code':'Interco code'}
                result6.rename(columns=Colname , inplace= True)

                final_result = result6.to_html(index=False, classes='table table-bordered table-sm ' , header = "true", justify = "center")
                
                #pivot                
                # table = pd.pivot_table(result6.round({'RPT amount':2}), 
                #     values=['RPT amount'],
                #     index=['Account type', 'Account subtype', 'WK group row','WK group name','Interco code'], #แกนด้านซ้าย
                #     columns=['Company code'],            
                #     aggfunc={'RPT amount': np.sum},
                #     fill_value=0,
                #     margins=True, #subtotal
                #     )    
                # final_pivot = table
                
        return render(request, 'RptResult.html', {'form': form,'final_result':final_result})
    else:
        form = InterCoForm()
    return render(request,'RptResult.html',{'form': form,'final_pivot':final_pivot})

############### Reclass ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def ReclassCreate(request):
    data = request.POST.copy()
    user_company_code = request.user.company_code
    # ReclassFormset = formset_factory(ReclassForm, extra=10 ,can_delete=True)
    ReclassHeader = JournalHeader.objects.all()
    if request.method == 'POST':
        form = ReclassHeaderForm(request.POST,prefix='form', user_company_code = request.user.company_code)
        formset = ReclassFormset(request.POST,prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
        a = form.is_valid()
        b = formset.is_valid()
        print(a)  
        print(b)   
        print(formset.errors)
        if form.is_valid() and formset.is_valid():
            #สร้าง Running Journal_no
            comcode = request.user.company_code
            print(comcode)
            last_journal = JournalHeader.objects.filter(Parent_company_code=comcode).order_by('journal_no').last()
            if not last_journal:
                new_journal_no = str(comcode) + '_JV_00001'
            else :
                journal_no = last_journal.journal_no
                journal_int = int(journal_no.split('_JV_')[-1])
                new_journal_int = journal_int + 1
                new_journal_str = str(new_journal_int).zfill(5)
                new_journal_no = str(comcode) + '_JV_' + new_journal_str
            #Condition check sum
            check_sum = 0 
            sum_debit = 0
            sum_credit = 0 #กำหนดค่าเริ่มต้นเท่ากัน 0
            i=0
            r=0
            for row in formset:
                if row.cleaned_data!= {}:
                    # sum_debit += float(row.data['formset-'+str(i)+'-debit']or 0)
                    # i=i+1
                    # sum_credit += float(row.data['formset-'+str(i)+'-credit'] or 0 )
                    # i=i+1
                    sum_debit += float(row.cleaned_data['debit'] or 0)
                    sum_credit += float(row.cleaned_data['credit'] or 0)
                    check_sum = sum_debit - sum_credit  #เอา field amount เก็บค่าเข้าตัวแปร  check_sum     
                    sum_total =  float(format(-check_sum , '.2f'))   #แปลงค่า ให้เป็น float ทศนิยม
                    # print(check_sum)
            if (sum_total == 0.00): 
            # บันทึกข้อมูล
                with transaction.atomic():
                    headerform = form.save(commit=False)
                    headerform.journal_no = new_journal_no
                    headerform.Parent_company_code = str(comcode)
                    headerform.journal_type = 'Reclassify'
                    headerform_save = form.save()
                    print(headerform.id)
                    for r in formset:
                        if r.cleaned_data != {}:
                            row = r.save(commit=False)
                            row.JournalHeader =  JournalHeader.objects.get(id=headerform.id) 
                            row.journal_no = headerform.journal_no
                            row.save()
                    # if  form.is_valid():
                    #     form.save(commit=False)
                    #     if formset.is_valid():
                    #         ReclassFormset.save(commit=False)
                    #         ReclassFormset.Journal_no = form.cleaned_data['id']
                    #         ReclassFormset.save(True)
                    #     form.save()
                messages.success(request, 'Your journal was create successfully!')
                return redirect(reverse('ReclassCreate')) 
            else:
                messages.warning(request ,'Validation! Transaction unbalance')
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        form = ReclassHeaderForm(prefix='form', user_company_code = request.user.company_code)
        # form.fields['account_code'].queryset = COA_Master.objects.filter(company_code =request.user.company_code)
        formset = ReclassFormset(prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
    return render(request, 'ReclassCreate.html', {'form': form, 'formset': formset})

@login_required(login_url='Login')
@user_passes_test(is_in_user_groups)
def ReclassCreateHeader(request):
    if request.method == 'POST':
        form = ReclassHeaderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your company was create successfully!')
            return redirect(reverse('ReclassCreateHeader')) 
    else:
        form = ReclassHeaderForm()    
    return render(request, 'ReclassCreateHeader.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def ReclassSummary(request):
    user_company_code = request.user.company_code
    data = JournalHeader.objects.filter(journal_type='Reclassify',Parent_company_code=user_company_code).order_by('journal_no')    
    journalFilter = JournalFilter(request.GET, queryset = data)
    data = journalFilter.qs
    return render(request, 'ReclassSummary.html', {'data': data, 'journalFilter':journalFilter })

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def ReclassUpdate(request, id, JournalHeader_pk=None):
    my_journal = JournalHeader.objects.get(id=id)
    journal = Journals.objects.filter(JournalHeader = my_journal)
    if request.method == 'POST' :
        form = ReclassHeaderForm(data =request.POST or None, instance = my_journal, prefix='form', user_company_code = request.user.company_code)
        formset = ReclassFormset(data =request.POST or None, instance=my_journal,prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
        Docno = JournalHeader.objects.get(id=id).journal_no
        # if form.is_valid() and formset.is_valid():
        if formset.is_valid():
            #Condition check sum
            check_sum = 0 
            sum_debit = 0
            sum_credit = 0 #กำหนดค่าเริ่มต้นเท่ากัน 0
            i=0
            r=0
            for row in formset:
                if row.cleaned_data!= {}:
                    # sum_debit += float(row.data['formset-'+str(i)+'-debit']or 0)
                    # i=i+1
                    # sum_credit += float(row.data['formset-'+str(i)+'-credit'] or 0 )
                    # i=i+1
                    sum_debit += float(row.cleaned_data['debit'] or 0)
                    sum_credit += float(row.cleaned_data['credit'] or 0)
                    check_sum = sum_debit - sum_credit  #เอา field amount เก็บค่าเข้าตัวแปร  check_sum     
                    sum_total =  float(format(-check_sum , '.2f'))   #แปลงค่า ให้เป็น float ทศนิยม
                    # print(check_sum)
            if (sum_total == 0.00): 
            # บันทึกข้อมูล
                for row in formset:
                    if row.cleaned_data != {}:
                        updateData = row.save(commit=False)
                        updateData.JournalHeader =  JournalHeader.objects.get(id=id)
                        updateData.journal_no = Docno
                        updateData.save()
                messages.success(request, 'Your Company was updated successfully!')
            else:
                messages.warning(request ,'Validation! Transaction unbalance')
        else: 
            messages.warning(request ,'Validation! Some value already exists')
            print(formset.errors)
    else:  
        form = ReclassHeaderForm(initial=my_journal.__dict__,prefix='form', user_company_code = request.user.company_code)
        formset = ReclassFormset(instance=my_journal,prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
        form.fields['company_code'].disabled = True
        form.fields['Parent_company_code'].disabled = True
        form.fields['period_code'].disabled = True
    return render(request, 'ReclassUpdate.html', {'form': form, 'formset': formset,'my_journal':my_journal} )

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def ReclassHeaderDelete(request, id):
    user_company_code = request.user.company_code
    JournalHeader.objects.get(id=id).delete()
    data = JournalHeader.objects.filter(journal_type='Reclassify',Parent_company_code=user_company_code)[:10]
    return render(request, 'ReclassSummary.html', {'data': data})
    
# def ReclassDetailDelete(request, id):
#     Journals.objects.get(id=id).delete()
#     data = Journals.objects.filter()[:10]
#     return render(request, 'ReclassUpdate.html', {'data': data})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def ReclassDetail(request,id):
    ReclassHeader = JournalHeader.objects.get(id=id)
    data = Journals.objects.filter(JournalHeader = ReclassHeader)
    sum_debit =  Journals.objects.filter(JournalHeader = ReclassHeader).aggregate(Sum('debit'))
    sum_credit =  Journals.objects.filter(JournalHeader = ReclassHeader).aggregate(Sum('credit'))

    return render(request,'ReclassDetail.html',{'ReclassHeader':ReclassHeader, 'data': data,'sum_debit':sum_debit,'sum_credit':sum_credit})

############### TakeEq ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TakeEqCreate(request):
    data = request.POST.copy()
    user_company_code = request.user.company_code
    TakeEqHeader = JournalHeader.objects.all()
    if request.method == 'POST':
        form = TakeEqHeaderForm(request.POST,prefix='form', user_company_code = request.user.company_code)
        formset = TakeEqFormset(request.POST,prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
        a = form.is_valid()
        b = formset.is_valid()
        print(a)  
        print(b)   
        print(formset.errors)
        if form.is_valid() and formset.is_valid():
            #สร้าง Running Journal_no
            comcode = request.user.company_code
            print(comcode)
            last_journal = JournalHeader.objects.filter(Parent_company_code=comcode).order_by('journal_no').last()
            if not last_journal:
                new_journal_no = comcode + '_JV_00001'
            else :
                journal_no = last_journal.journal_no
                journal_int = int(journal_no.split('_JV_')[-1])
                new_journal_int = journal_int + 1
                new_journal_str = str(new_journal_int).zfill(5)
                new_journal_no = str(comcode) + '_JV_' + new_journal_str
            #Condition check sum
            check_sum = 0 
            sum_debit = 0
            sum_credit = 0 #กำหนดค่าเริ่มต้นเท่ากัน 0
            for row in formset:
                if row.cleaned_data!= {}:
                    sum_debit += float(row.cleaned_data['debit'] or 0)
                    sum_credit += float(row.cleaned_data['credit'] or 0)
                    check_sum = sum_debit - sum_credit  #เอา field amount เก็บค่าเข้าตัวแปร  check_sum     
                    sum_total =  float(format(-check_sum , '.2f'))   #แปลงค่า ให้เป็น float ทศนิยม
                    # print(check_sum)
            if (sum_total == 0.00): 
            # บันทึกข้อมูล
                with transaction.atomic():
                    headerform = form.save(commit=False)
                    headerform.journal_no = new_journal_no
                    headerform.Parent_company_code = str(comcode)
                    headerform.journal_type = 'TakeEq'
                    headerform_save = form.save()
                    for r in formset:
                        if r.cleaned_data != {}:
                            row = r.save(commit=False)
                            row.JournalHeader =  JournalHeader.objects.get(id=headerform.id) 
                            row.journal_no = headerform.journal_no
                            row.save()
                messages.success(request, 'Your journal was create successfully!')
                return redirect(reverse('TakeEqCreate')) 
            else:
                messages.warning(request ,'Validation! Transaction unbalance')
        else:
            messages.warning(request ,'Validation! Some value already exists')
    else:
        form = TakeEqHeaderForm(prefix='form', user_company_code = request.user.company_code)
        formset = TakeEqFormset(prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
    return render(request, 'TakeEqCreate.html', {'form': form, 'formset': formset})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TakeEqCreateHeader(request):
    if request.method == 'POST':
        form = TakeEqHeaderForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your company was create successfully!')
            return redirect(reverse('TakeEqCreateHeader')) 
    else:
        form = TakeEqHeaderForm()    
    return render(request, 'TakeEqCreateHeader.html', {'form': form})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TakeEqSummary(request):
    user_company_code = request.user.company_code
    data = JournalHeader.objects.filter(journal_type='TakeEq',Parent_company_code=user_company_code).order_by('journal_no')    
    journalFilter = JournalFilter(request.GET, queryset = data)
    data = journalFilter.qs
    return render(request, 'TakeEqSummary.html', {'data': data, 'journalFilter':journalFilter })

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TakeEqUpdate(request, id, JournalHeader_pk=None):
    my_journal = JournalHeader.objects.get(id=id)
    journal = Journals.objects.filter(JournalHeader = my_journal)
    if request.method == 'POST' :
        form = TakeEqHeaderForm(data =request.POST or None, instance = my_journal, prefix='form', user_company_code = request.user.company_code)
        formset = TakeEqFormset(data =request.POST or None, instance=my_journal,prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
        Docno = JournalHeader.objects.get(id=id).journal_no
        # if form.is_valid() and formset.is_valid():
        if formset.is_valid():
            #Condition check sum
            check_sum = 0 
            sum_debit = 0
            sum_credit = 0 #กำหนดค่าเริ่มต้นเท่ากัน 0
            i=0
            r=0
            for row in formset:
                if row.cleaned_data!= {}:
                    # sum_debit += float(row.data['formset-'+str(i)+'-debit']or 0)
                    # i=i+1
                    # sum_credit += float(row.data['formset-'+str(i)+'-credit'] or 0 )
                    # i=i+1
                    sum_debit += float(row.cleaned_data['debit'] or 0)
                    sum_credit += float(row.cleaned_data['credit'] or 0)
                    check_sum = sum_debit - sum_credit  #เอา field amount เก็บค่าเข้าตัวแปร  check_sum     
                    sum_total =  float(format(-check_sum , '.2f'))   #แปลงค่า ให้เป็น float ทศนิยม
                    # print(check_sum)
            if (sum_total == 0.00): 
            # บันทึกข้อมูล
                for row in formset:
                    if row.cleaned_data != {}:
                        updateData = row.save(commit=False)
                        updateData.JournalHeader =  JournalHeader.objects.get(id=id)
                        updateData.journal_no = Docno
                        updateData.save()
                messages.success(request, 'Your Company was updated successfully!')
            else:
                messages.warning(request ,'Validation! Transaction unbalance')
        else: 
            messages.warning(request ,'Validation! Some value already exists')
            print(formset.errors)
    else:  
        form = TakeEqHeaderForm(initial=my_journal.__dict__,prefix='form', user_company_code = request.user.company_code)
        formset = TakeEqFormset(instance=my_journal,prefix='formset',form_kwargs={'user_company_code': request.user.company_code})
        form.fields['company_code'].disabled = True
        form.fields['Parent_company_code'].disabled = True
        form.fields['period_code'].disabled = True
    return render(request, 'TakeEqUpdate.html', {'form': form, 'formset': formset,'my_journal':my_journal} )\

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TakeEqHeaderDelete(request, id):
    user_company_code = request.user.company_code
    JournalHeader.objects.get(id=id).delete()
    data = JournalHeader.objects.filter(journal_type='TakeEq',Parent_company_code=user_company_code)[:10]
    return render(request, 'TakeEqSummary.html', {'data': data})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def TakeEqDetail(request,id):
    TakeEqHeader = JournalHeader.objects.get(id=id)
    data = Journals.objects.filter(JournalHeader = TakeEqHeader)
    sum_debit =  Journals.objects.filter(JournalHeader = TakeEqHeader).aggregate(Sum('debit'))
    sum_credit =  Journals.objects.filter(JournalHeader = TakeEqHeader).aggregate(Sum('credit'))
    return render(request,'TakeEqDetail.html',{'TakeEqHeader':TakeEqHeader, 'data': data,'sum_debit':sum_debit,'sum_credit':sum_credit})

############### Working ###############
@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def Working_bs(request):
    user_com_code = request.user.company_code
    final_pivot = ''
    if request.method == "POST":
        form = WorkingForm(request.POST)
        period = request.POST['PeriodsFilter']
        if form.is_valid():
            company_list = Company_Master.objects.filter(parent_company=user_com_code).values('company_code')
            pd.options.display.float_format = "{:,.2f}".format
            ## import model
            TB = pd.DataFrame(list(Trial_balance.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','tb_amount')))
            df_interco = pd.DataFrame(list(Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','rpt_amount')))
            df_journalHeader = pd.DataFrame(list(JournalHeader.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('journal_no','period_code','company_code','journal_type')))
            df_journal = pd.DataFrame(list(Journals.objects.all().values('journal_no','account_code','journal_amount')))
            df_company = pd.DataFrame(list(Company_Master.objects.values('company_code','company_type','parent_company')))
            df_coa = pd.DataFrame(list(COA_Master.objects.filter(company_code__in = company_list).values('company_code','account_code','account_name','wk_group_row')))
            df_fsgroup = pd.DataFrame(list(FS_grouping_Master.objects.filter(company_code = user_com_code).values('company_code','fs_group_row','fs_group_name','wk_group_row','wk_group_name','account_type','account_subtype')))

            ## Join table
            if TB.empty and df_interco.empty and df_journalHeader.empty :
                messages.warning(request ,'No data found!')
                return redirect(reverse('Working_bs'))
            else:
                if not TB.empty:
                    df_TB = pd.pivot_table(TB,values = 'tb_amount', index=['account_code','period_code','company_code'], columns='company_code', aggfunc='sum',fill_value=0,margins=True, margins_name='Total TB')
                    df_TB.reset_index(inplace=True)
                    df_TB2 = df_TB.iloc[:-1]
                    resultTB = pd.merge(df_TB2, df_company, on=['company_code'], how='left')
                    resultTB2 = pd.merge(resultTB, df_coa, on=['account_code','company_code'], how='left')
                    resultTB3 = pd.merge(resultTB2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultTB4 = resultTB3.drop(columns=['period_code','account_code','account_name','fs_group_row','fs_group_name','company_type','parent_company','company_code_x','company_code_y'])
                    resultTB4['wk_group_row'] = resultTB4['wk_group_row'].fillna('n/a group')
                    resultTB4['wk_group_name'] = resultTB4['wk_group_name'].fillna('n/a group')
                    resultTB4['account_type'] = resultTB4['account_type'].fillna('n/a group')
                    resultTB4['account_subtype'] = resultTB4['account_subtype'].fillna('n/a group')
                    resultTB5 = resultTB4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                    resultTB6 = resultTB5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultTB6 = "Null"

                if not df_interco.empty:
                    resultInterco = pd.merge(df_interco, df_company, on=['company_code'], how='left')
                    resultInterco2 = pd.merge(resultInterco, df_coa, on=['account_code','company_code'], how='left')
                    resultInterco3 = pd.merge(resultInterco2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultInterco4 = resultInterco3.drop(columns=['period_code','account_code', 'account_name','fs_group_row','fs_group_name','company_type','parent_company','company_code_x','company_code_y'])
                    resultInterco4['wk_group_row'] = resultInterco4['wk_group_row'].fillna('n/a group')
                    resultInterco4['wk_group_name'] = resultInterco4['wk_group_name'].fillna('n/a group')
                    resultInterco4['account_type'] = resultInterco4['account_type'].fillna('n/a group')
                    resultInterco4['account_subtype'] = resultInterco4['account_subtype'].fillna('n/a group')
                    resultInterco4['rpt_amount'] = resultInterco4['rpt_amount'].fillna('0.00')
                    resultInterco5 = resultInterco4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                    resultInterco6 = resultInterco5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultInterco6 = "Null"

                if not df_journalHeader.empty:
                    resultJV = pd.merge(df_journalHeader, df_journal, on=['journal_no'], how='left')
                    resultJV2 = pd.merge(resultJV, df_company, on=['company_code'], how='left')
                    resultJV3 = pd.merge(resultJV2, df_coa, on=['account_code','company_code'], how='left')
                    resultJV4 = pd.merge(resultJV3, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    ### เเยก Reclass กับ TakeEq
                    resultJV4['reclass_amount'] = resultJV4.loc[resultJV['journal_type']== 'Reclassify', 'journal_amount']
                    resultJV4.append(resultJV4.sum(numeric_only=True),ignore_index=True)
                    resultJV4['reclass_amount'] = resultJV4['reclass_amount'].fillna('0.00')
                    resultJV4['takeEq_amount'] = resultJV4.loc[resultJV['journal_type']== 'TakeEq', 'journal_amount']
                    resultJV4.append(resultJV4.sum(numeric_only=True),ignore_index=True)
                    resultJV4['takeEq_amount'] = resultJV4['takeEq_amount'].fillna('0.00')
                    resultJV4_1 = resultJV4.apply(pd.to_numeric, errors='ignore')
                    # resultJV4_1 = resultJV4.set_index(['takeEq_amount','reclass_amount','account_type', 'account_subtype', 'wk_group_row','wk_group_name','period_code', 'journal_no','company_type','parent_company','company_code_y'])
                    resultJV4_2 = resultJV4_1.drop(columns=['period_code','journal_no','company_type','parent_company','company_code_y'])
                    resultJV4_3 = pd.pivot_table(resultJV4_2, values = 'reclass_amount', index=['account_code','account_name','wk_group_row','wk_group_name','fs_group_row','fs_group_name','account_type','account_subtype'], columns=['company_code_x'], aggfunc='sum',fill_value=0)
                    resultJV4_4 = resultJV4_2.drop(columns=['journal_type','journal_amount','company_code_x'])
                    resultJV5 = resultJV4_4.groupby(['account_code','account_name', 'wk_group_row','wk_group_name', 'fs_group_row','fs_group_name','account_type','account_subtype'], dropna=False).sum().reset_index()
                    resultJV6 = pd.merge(resultJV5, resultJV4_3, on=['wk_group_row','wk_group_name', 'fs_group_row','fs_group_name','account_type','account_subtype'], how='outer')
                    
                    resultJV6_1 = resultJV6.drop(columns=['account_code','account_name'])
                    # resultJV5['wk_group_row'] = resultJV5['wk_group_row'].fillna('n/a group')
                    # resultJV5['wk_group_name'] = resultJV5['wk_group_name'].fillna('n/a group')
                    # resultJV5['account_type'] = resultJV5['account_type'].fillna('n/a group')
                    # resultJV5['account_subtype'] = resultJV5['account_subtype'].fillna('n/a group')
                    resultJV7 = resultJV6_1.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                    
                else:
                    resultJV7 = "Null"

                if not TB.empty and not df_interco.empty and not df_journalHeader.empty :
                    result0 = resultTB6.append(resultJV7, sort=False)
                    result = result0.append(resultInterco6, sort=False)
                    # result0 = resultTB6.append(resultInterco6, sort=False)
                    # result = result0.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB'] + result2['reclass_amount'] 
                    result2['Total Conso'] = result2['Total TB'] + result2['rpt_amount'] + result2['reclass_amount'] + result2['takeEq_amount']

                elif not TB.empty and not df_interco.empty :
                    result = resultTB6.append(resultInterco6, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB'] 
                    result2['Total Conso'] = result2['Total TB'] + result2['rpt_amount'] 
                    
                elif not df_interco.empty and not df_journalHeader.empty :
                    result = resultInterco6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = 0
                    result2['Total Conso'] = result2['rpt_amount'] + result2['reclass_amount'] + result2['takeEq_amount']
                
                elif not TB.empty and not df_journalHeader.empty :
                    result = resultTB6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB'] + result2['reclass_amount'] 
                    result2['Total Conso'] = result2['Total TB'] + result2['reclass_amount'] + result2['takeEq_amount']
                    
                elif not TB.empty :
                    result = resultTB6
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB']
                    result2['Total Conso'] = result2['Total TB'] 

                elif not df_interco.empty :
                    result = resultInterco6
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = 0
                    result2['Total Conso'] =  result2['rpt_amount'] 

                elif not df_journalHeader.empty :
                    result = resultJV7
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['reclass_amount']
                    result2['Total Conso'] = result2['reclass_amount'] + result2['takeEq_amount']
                else:
                    messages.warning(request ,'No data found!')

                result2.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                result3 = result2.drop(columns=['Total TB','reclass_amount'])

                cols_at_end = ['Total Separate','rpt_amount','takeEq_amount','Total Conso']
                result4 = result3[[c for c in result3 if c not in cols_at_end] + [c for c in cols_at_end if c in result3]]

                result5 = result4.loc[result4['account_type'].isin(['สินทรัพย์','หนี้สิน','ส่วนของผู้ถือหุ้น','n/a group'])]
                result5.loc["Total"] = result5.sum(numeric_only=True, axis=0)
                result5.append(result5.sum(numeric_only=True),ignore_index=True)
                result5[['wk_group_name']] = result5[['wk_group_name']].fillna(value='Total')
                result5.fillna('',inplace=True)
                Col = {'account_type':'Account type', 'account_subtype':'Account subtype', 'wk_group_row':'WK group row','wk_group_name':'WK group name','rpt_amount':'Eliminate','takeEq_amount':'Take equity'}
                result5.rename(columns=Col , inplace= True)

                final_result = result5.to_html(index=False, classes='table table-bordered table-sm' , header = "true", justify = "center")
               
        return render(request, 'Working_bs.html',{'form':form,'final_result':final_result})
    else:
        form = WorkingForm()
    return render(request,'Working_bs.html',{'form':form,})

@user_passes_test(is_in_user_groups)
@login_required(login_url='Login')
def Working_pl(request):
    user_com_code = request.user.company_code
    final_pivot = ''
    if request.method == "POST":
        form = WorkingForm(request.POST)
        period = request.POST['PeriodsFilter']
        if form.is_valid():
            company_list = Company_Master.objects.filter(parent_company=user_com_code).values('company_code')
            pd.options.display.float_format = "{:,.2f}".format
            ## import model
            TB = pd.DataFrame(list(Trial_balance.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','tb_amount')))
            df_interco = pd.DataFrame(list(Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','rpt_amount')))
            df_journalHeader = pd.DataFrame(list(JournalHeader.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('journal_no','period_code','company_code','journal_type')))
            df_journal = pd.DataFrame(list(Journals.objects.all().values('journal_no','account_code','journal_amount')))
            df_company = pd.DataFrame(list(Company_Master.objects.values('company_code','company_type','parent_company')))
            df_coa = pd.DataFrame(list(COA_Master.objects.filter(company_code__in = company_list).values('company_code','account_code','account_name','wk_group_row')))
            df_fsgroup = pd.DataFrame(list(FS_grouping_Master.objects.filter(company_code = user_com_code).values('company_code','fs_group_row','fs_group_name','wk_group_row','wk_group_name','account_type','account_subtype')))

            ## Join table
            if TB.empty and df_interco.empty and df_journalHeader.empty :
                messages.warning(request ,'No data found!')
                return redirect(reverse('Working_bs'))
            else:
                if not TB.empty:
                    df_TB = pd.pivot_table(TB,values = 'tb_amount', index=['account_code','period_code','company_code'], columns='company_code', aggfunc='sum',fill_value=0,margins=True, margins_name='Total TB')
                    df_TB.reset_index(inplace=True)
                    df_TB2 = df_TB.iloc[:-1]
                    resultTB = pd.merge(df_TB2, df_company, on=['company_code'], how='left')
                    resultTB2 = pd.merge(resultTB, df_coa, on=['account_code','company_code'], how='left')
                    resultTB3 = pd.merge(resultTB2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultTB4 = resultTB3.drop(columns=['period_code','account_code','account_name','fs_group_row','fs_group_name','company_type','parent_company','company_code_x','company_code_y'])
                    resultTB4['wk_group_row'] = resultTB4['wk_group_row'].fillna('n/a group')
                    resultTB4['wk_group_name'] = resultTB4['wk_group_name'].fillna('n/a group')
                    resultTB4['account_type'] = resultTB4['account_type'].fillna('n/a group')
                    resultTB4['account_subtype'] = resultTB4['account_subtype'].fillna('n/a group')
                    resultTB5 = resultTB4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                    resultTB6 = resultTB5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultTB6 = "Null"

                if not df_interco.empty:
                    resultInterco = pd.merge(df_interco, df_company, on=['company_code'], how='left')
                    resultInterco2 = pd.merge(resultInterco, df_coa, on=['account_code','company_code'], how='left')
                    resultInterco3 = pd.merge(resultInterco2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultInterco4 = resultInterco3.drop(columns=['period_code','account_code', 'account_name','fs_group_row','fs_group_name','company_type','parent_company','company_code_x','company_code_y'])
                    resultInterco4['wk_group_row'] = resultInterco4['wk_group_row'].fillna('n/a group')
                    resultInterco4['wk_group_name'] = resultInterco4['wk_group_name'].fillna('n/a group')
                    resultInterco4['account_type'] = resultInterco4['account_type'].fillna('n/a group')
                    resultInterco4['account_subtype'] = resultInterco4['account_subtype'].fillna('n/a group')
                    resultInterco4['rpt_amount'] = resultInterco4['rpt_amount'].fillna('0.00')
                    resultInterco5 = resultInterco4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                    resultInterco6 = resultInterco5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultInterco6 = "Null"

                if not df_journalHeader.empty:
                    resultJV = pd.merge(df_journalHeader, df_journal, on=['journal_no'], how='left')
                    resultJV2 = pd.merge(resultJV, df_company, on=['company_code'], how='left')
                    resultJV3 = pd.merge(resultJV2, df_coa, on=['account_code','company_code'], how='left')
                    resultJV4 = pd.merge(resultJV3, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    ### เเยก Reclass กับ TakeEq
                    resultJV4['reclass_amount'] = resultJV4.loc[resultJV['journal_type']== 'Reclassify', 'journal_amount']
                    resultJV4.append(resultJV4.sum(numeric_only=True),ignore_index=True)
                    resultJV4['reclass_amount'] = resultJV4['reclass_amount'].fillna('0.00')
                    resultJV4['takeEq_amount'] = resultJV4.loc[resultJV['journal_type']== 'TakeEq', 'journal_amount']
                    resultJV4.append(resultJV4.sum(numeric_only=True),ignore_index=True)
                    resultJV4['takeEq_amount'] = resultJV4['takeEq_amount'].fillna('0.00')
                    resultJV4_1 = resultJV4.apply(pd.to_numeric, errors='ignore')
                    # resultJV4_1 = resultJV4.set_index(['takeEq_amount','reclass_amount','account_type', 'account_subtype', 'wk_group_row','wk_group_name','period_code', 'journal_no','company_type','parent_company','company_code_y'])
                    resultJV4_2 = resultJV4_1.drop(columns=['period_code','journal_no','company_type','parent_company','company_code_y'])
                    resultJV4_3 = pd.pivot_table(resultJV4_2, values = 'reclass_amount', index=['account_code','account_name','wk_group_row','wk_group_name','fs_group_row','fs_group_name','account_type','account_subtype'], columns=['company_code_x'], aggfunc='sum',fill_value=0)
                    resultJV4_4 = resultJV4_2.drop(columns=['journal_type','journal_amount','company_code_x'])
                    resultJV5 = resultJV4_4.groupby(['account_code','account_name', 'wk_group_row','wk_group_name', 'fs_group_row','fs_group_name','account_type','account_subtype'], dropna=False).sum().reset_index()
                    resultJV6 = pd.merge(resultJV5, resultJV4_3, on=['wk_group_row','wk_group_name', 'fs_group_row','fs_group_name','account_type','account_subtype'], how='outer')
                    
                    resultJV6_1 = resultJV6.drop(columns=['account_code','account_name'])
                    # resultJV5['wk_group_row'] = resultJV5['wk_group_row'].fillna('n/a group')
                    # resultJV5['wk_group_name'] = resultJV5['wk_group_name'].fillna('n/a group')
                    # resultJV5['account_type'] = resultJV5['account_type'].fillna('n/a group')
                    # resultJV5['account_subtype'] = resultJV5['account_subtype'].fillna('n/a group')
                    resultJV7 = resultJV6_1.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                    
                else:
                    resultJV7 = "Null"

                if not TB.empty and not df_interco.empty and not df_journalHeader.empty :
                    result0 = resultTB6.append(resultJV7, sort=False)
                    result = result0.append(resultInterco6, sort=False)
                    # result0 = resultTB6.append(resultInterco6, sort=False)
                    # result = result0.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB'] + result2['reclass_amount'] 
                    result2['Total Conso'] = result2['Total TB'] + result2['rpt_amount'] + result2['reclass_amount'] + result2['takeEq_amount']

                elif not TB.empty and not df_interco.empty :
                    result = resultTB6.append(resultInterco6, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB'] 
                    result2['Total Conso'] = result2['Total TB'] + result2['rpt_amount'] 
                    
                elif not df_interco.empty and not df_journalHeader.empty :
                    result = resultInterco6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = 0
                    result2['Total Conso'] = result2['rpt_amount'] + result2['reclass_amount'] + result2['takeEq_amount']
                
                elif not TB.empty and not df_journalHeader.empty :
                    result = resultTB6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB'] + result2['reclass_amount'] 
                    result2['Total Conso'] = result2['Total TB'] + result2['reclass_amount'] + result2['takeEq_amount']
                    
                elif not TB.empty :
                    result = resultTB6
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['Total TB']
                    result2['Total Conso'] = result2['Total TB'] 

                elif not df_interco.empty :
                    result = resultInterco6
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = 0
                    result2['Total Conso'] =  result2['rpt_amount'] 

                elif not df_journalHeader.empty :
                    result = resultJV7
                    result2 = result.groupby(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'], dropna=False).sum().reset_index().sort_values('wk_group_row', ascending=True)
                    result2['Total Separate'] = result2['reclass_amount']
                    result2['Total Conso'] = result2['reclass_amount'] + result2['takeEq_amount']
                else:
                    messages.warning(request ,'No data found!')

                result2.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name'])
                result3 = result2.drop(columns=['Total TB','reclass_amount'])
                
                cols_at_end = ['Total Separate','rpt_amount','takeEq_amount','Total Conso']
                result4 = result3[[c for c in result3 if c not in cols_at_end] + [c for c in cols_at_end if c in result3]]
                result5 = result4.loc[result4['account_type'].isin(['รายได้','ค่าใช้จ่าย'])]
                cols = result5.index
                #### iloc ใช้แทนลำดับ row,Col
                result5.iloc[:,4:] = result5.iloc[:,4:].mul(-1)
                result5.loc["Total"] = result5.sum(numeric_only=True, axis=0)
                result5.append(result5.sum(numeric_only=True),ignore_index=True)
                result5[['wk_group_name']] = result5[['wk_group_name']].fillna(value='Total')
                result5.fillna('',inplace=True)
                Col = {'account_type':'Account type', 'account_subtype':'Account subtype', 'wk_group_row':'WK group row','wk_group_name':'WK group name','rpt_amount':'Eliminate','takeEq_amount':'Take equity'}
                result5.rename(columns=Col , inplace= True)

                final_result = result5.to_html(index=False,classes='table table-bordered table-sm' , header = "true", justify = "center")
               
        return render(request, 'Working_pl.html',{'form':form,'final_result':final_result})
    else:
        form = WorkingForm()
    return render(request,'Working_pl.html',{'form':form,})

# def Report_bs(request):
#     return render(request,'Report_bs.html')   
# def Report_pl(request):
#     return render(request,'Report_pl.html') 

############### Report ###############
@user_passes_test(is_in_all_groups)
@login_required(login_url='Login')
def Report_bs(request):
    user_com_code = request.user.company_code
    final_pivot = ''
    if request.method == "POST":
        form = WorkingForm(request.POST)
        period = request.POST['PeriodsFilter']
        if form.is_valid():
            company_list = Company_Master.objects.filter(parent_company=user_com_code).values('company_code')
            pd.options.display.float_format = "{:,.2f}".format
            ## import model
            TB = pd.DataFrame(list(Trial_balance.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','tb_amount')))
            df_interco = pd.DataFrame(list(Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','rpt_amount')))
            df_journalHeader = pd.DataFrame(list(JournalHeader.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('journal_no','period_code','company_code','journal_type')))
            df_journal = pd.DataFrame(list(Journals.objects.all().values('journal_no','account_code','journal_amount')))
            df_company = pd.DataFrame(list(Company_Master.objects.values('company_code','company_type','parent_company')))
            df_coa = pd.DataFrame(list(COA_Master.objects.filter(company_code__in = company_list).values('company_code','account_code','account_name','wk_group_row')))
            df_fsgroup = pd.DataFrame(list(FS_grouping_Master.objects.filter(company_code = user_com_code).values('company_code','fs_group_row','fs_group_name','wk_group_row','wk_group_name','account_type','account_subtype')))

            ## Join table
            if TB.empty and df_interco.empty and df_journalHeader.empty :
                messages.warning(request ,'No data found!')
                return redirect(reverse('Report_bs'))
            else:
                if not TB.empty:
                    df_TB = pd.pivot_table(TB,values = 'tb_amount', index=['account_code','period_code','company_code'], columns='company_code', aggfunc='sum',fill_value=0,margins=True, margins_name='Total TB')
                    df_TB.reset_index(inplace=True)
                    df_TB2 = df_TB.iloc[:-1]
                    resultTB = pd.merge(df_TB2, df_company, on=['company_code'], how='left')
                    resultTB2 = pd.merge(resultTB, df_coa, on=['account_code','company_code'], how='left')
                    resultTB3 = pd.merge(resultTB2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultTB4 = resultTB3.drop(columns=['period_code','account_code','account_name','company_type'])
                    resultTB4['wk_group_row'] = resultTB4['wk_group_row'].fillna('n/a group')
                    resultTB4['wk_group_name'] = resultTB4['wk_group_name'].fillna('n/a group')
                    resultTB4['fs_group_row'] = resultTB4['fs_group_row'].fillna('n/a group')
                    resultTB4['fs_group_name'] = resultTB4['fs_group_name'].fillna('n/a group')
                    resultTB4['account_type'] = resultTB4['account_type'].fillna('n/a group')
                    resultTB4['account_subtype'] = resultTB4['account_subtype'].fillna('n/a group')
                    resultTB5 = resultTB4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','fs_group_row','fs_group_name'])
                    resultTB6 = resultTB5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultTB6 = "Null"

                if not df_interco.empty:
                    resultInterco = pd.merge(df_interco, df_company, on=['company_code'], how='left')
                    resultInterco2 = pd.merge(resultInterco, df_coa, on=['account_code','company_code'], how='left')
                    resultInterco3 = pd.merge(resultInterco2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultInterco4 = resultInterco3.drop(columns=['period_code','account_code', 'account_name','company_type'])
                    resultInterco4['wk_group_row'] = resultInterco4['wk_group_row'].fillna('n/a group')
                    resultInterco4['wk_group_name'] = resultInterco4['wk_group_name'].fillna('n/a group')
                    resultInterco4['fs_group_row'] = resultInterco4['fs_group_row'].fillna('n/a group')
                    resultInterco4['fs_group_name'] = resultInterco4['fs_group_name'].fillna('n/a group')
                    resultInterco4['account_type'] = resultInterco4['account_type'].fillna('n/a group')
                    resultInterco4['account_subtype'] = resultInterco4['account_subtype'].fillna('n/a group')
                    resultInterco4['rpt_amount'] = resultInterco4['rpt_amount'].fillna('0.00')
                    resultInterco5 = resultInterco4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','fs_group_row','fs_group_name'])
                    resultInterco6 = resultInterco5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultInterco6 = "Null"

                if not df_journalHeader.empty:
                    resultJV = pd.merge(df_journalHeader, df_journal, on=['journal_no'], how='left')
                    resultJV2 = pd.merge(resultJV, df_company, on=['company_code'], how='left')
                    resultJV3 = pd.merge(resultJV2, df_coa, on=['account_code','company_code'], how='left')
                    resultJV4 = pd.merge(resultJV3, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultJV5 = resultJV4.drop(columns=['period_code','account_code', 'journal_no','account_name','company_type'])
                    resultJV5['wk_group_row'] = resultJV5['wk_group_row'].fillna('n/a group')
                    resultJV5['wk_group_name'] = resultJV5['wk_group_name'].fillna('n/a group')
                    resultJV5['fs_group_row'] = resultJV5['fs_group_row'].fillna('n/a group')
                    resultJV5['fs_group_name'] = resultJV5['fs_group_name'].fillna('n/a group')
                    resultJV5['account_type'] = resultJV5['account_type'].fillna('n/a group')
                    resultJV5['account_subtype'] = resultJV5['account_subtype'].fillna('n/a group')
                    resultJV5['journal_amount'] = resultJV5['journal_amount'].fillna('0.00')
                    ### เเยก Reclass กับ TakeEq
                    resultJV5['reclass_amount'] = resultJV5.loc[resultJV5['journal_type']== 'Reclassify', 'journal_amount']
                    resultJV5['reclass_amount'] = resultJV5['reclass_amount'].fillna('0.00')
                    resultJV5['takeEq_amount'] = resultJV5.loc[resultJV5['journal_type']== 'TakeEq', 'journal_amount']
                    resultJV5['takeEq_amount'] = resultJV5['takeEq_amount'].fillna('0.00')
                    
                    resultJV6 = resultJV5.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','fs_group_row','fs_group_name'])
                    resultJV7 = resultJV6.apply(pd.to_numeric, errors='ignore')
                    ### เเยก Reclass กับ TakeEq
                    # resultJV7['reclass_amount'] = result3.loc[result3['journal_type']== 'Reclassify', ['Total TB','journal_amount']].sum(axis=1)
                    # resultJV7['takeEq_amount'] = result3.loc[result3['journal_type']== 'TakeEq', ['Total TB','journal_amount']].sum(axis=1)
                else:
                    resultJV7 = "Null"

                if not TB.empty and not df_interco.empty and not df_journalHeader.empty :
                    result0 = resultTB6.append(resultInterco6, sort=False)
                    result = result0.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype','fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] = result2['Total TB'] + result2['rpt_amount'] + result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = result3.loc[result3['company_code_x']== str(user_com_code), ['Total TB','reclass_amount']].sum(axis=1)
                    result3['Separate FS'].fillna(0, inplace=True)
                
                elif not TB.empty and not df_interco.empty :
                    result = resultTB6.append(resultInterco6, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] = result2['Total TB'] + result2['rpt_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB']].sum(axis=1)
                    result3['Separate FS'].fillna(0, inplace=True)
                    
                elif not df_interco.empty and not df_journalHeader.empty :
                    result = resultInterco6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype','fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] = result2['rpt_amount']  + result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB','reclass_amount']].sum(axis=1)
                    result3['Separate FS'].fillna(0, inplace=True)

                elif not TB.empty and not df_journalHeader.empty :
                    result = resultTB6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] = result2['Total TB']  + result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB','reclass_amount']].sum(axis=1)
                    result3['Separate FS'].fillna(0, inplace=True)

                elif not TB.empty :
                    result = resultTB6
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] = result2['Total TB']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB']].sum(axis=1)
                    result3['Separate FS'].fillna(0, inplace=True)

                elif not df_interco.empty :
                    result = resultInterco6
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] =  result2['rpt_amount'] 
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = "0"

                elif not df_journalHeader.empty :
                    result = resultJV7
                    result2 = result.groupby(['account_type', 'account_subtype','fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['Consolidated FS'] =  result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['Separate FS'] = result3.loc[result3['company_code_x']== str(user_com_code),['reclass_amount']].sum(axis=1)
                    result3['Separate FS'].fillna(0, inplace=True)
                else:
                    messages.warning(request ,'No data found!')

                result4 = result3[['account_type', 'account_subtype','fs_group_row','fs_group_name','Separate FS','Consolidated FS']]
                result4.set_index(['account_type', 'account_subtype', 'fs_group_row','fs_group_name'])
                result5 = result4.loc[result4['account_type'].isin(['สินทรัพย์','หนี้สิน','ส่วนของผู้ถือหุ้น','n/a group'])]
                result6 = result5.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                # result6['SeparateFS'] = np.where(result6.account_type == 'รายได้', result6.SeparateFS * -1, result6.SeparateFS)   
                result6.loc["Total"] = result5.sum(numeric_only=True, axis=0)
                result6.append(result5.sum(numeric_only=True),ignore_index=True)
                result6[['fs_group_name']] = result6[['fs_group_name']].fillna(value='Total')
                result6.fillna('', inplace=True)
                Colname = {'account_type':'Account type', 'account_subtype':'Account subtype', 'fs_group_row':'FS group row','fs_group_name':'FS group name'}
                result6.rename(columns=Colname , inplace= True)

                #HTML
                final_result = result6.to_html(index=False,classes='table table-bordered table-sm ' , header = "true", justify = "center")   
                
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                # writer = pd.ExcelWriter('BS_Statement.xlsx', engine='xlsxwriter')
                # result6.to_excel(writer, sheet_name='Sheet1', index=False)
                # writer.save()              

        return render(request, 'Report_bs.html',{'form':form,'final_result':final_result})
    else:
        form = WorkingForm()
    return render(request,'Report_bs.html',{'form':form})

@login_required(login_url='Login')
@user_passes_test(is_in_all_groups)
def Report_pl(request):
    user_com_code = request.user.company_code
    final_pivot = ''
    if request.method == "POST":
        form = WorkingForm(request.POST)
        period = request.POST['PeriodsFilter']
        if form.is_valid():
            company_list = Company_Master.objects.filter(parent_company=user_com_code).values('company_code')
            pd.options.display.float_format = "{:,.2f}".format
            ## import model
            TB = pd.DataFrame(list(Trial_balance.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','tb_amount')))
            df_interco = pd.DataFrame(list(Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('company_code','period_code','account_code','rpt_amount')))
            df_journalHeader = pd.DataFrame(list(JournalHeader.objects.filter(Q(company_code__in = company_list)&Q(period_code=period)).values('journal_no','period_code','company_code','journal_type')))
            df_journal = pd.DataFrame(list(Journals.objects.all().values('journal_no','account_code','journal_amount')))
            df_company = pd.DataFrame(list(Company_Master.objects.values('company_code','company_type','parent_company')))
            df_coa = pd.DataFrame(list(COA_Master.objects.filter(company_code__in = company_list).values('company_code','account_code','account_name','wk_group_row')))
            df_fsgroup = pd.DataFrame(list(FS_grouping_Master.objects.filter(company_code = user_com_code).values('company_code','fs_group_row','fs_group_name','wk_group_row','wk_group_name','account_type','account_subtype')))

            ## Join table
            if TB.empty and df_interco.empty and df_journalHeader.empty :
                messages.warning(request ,'No data found!')
                return redirect(reverse('Report_pl'))
            else:
                if not TB.empty:
                    df_TB = pd.pivot_table(TB,values = 'tb_amount', index=['account_code','period_code','company_code'], columns='company_code', aggfunc='sum',fill_value=0,margins=True, margins_name='Total TB')
                    df_TB.reset_index(inplace=True)
                    df_TB2 = df_TB.iloc[:-1]
                    resultTB = pd.merge(df_TB2, df_company, on=['company_code'], how='left')
                    resultTB2 = pd.merge(resultTB, df_coa, on=['account_code','company_code'], how='left')
                    resultTB3 = pd.merge(resultTB2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultTB4 = resultTB3.drop(columns=['period_code','account_code','account_name','company_type'])
                    resultTB4['wk_group_row'] = resultTB4['wk_group_row'].fillna('n/a group')
                    resultTB4['wk_group_name'] = resultTB4['wk_group_name'].fillna('n/a group')
                    resultTB4['fs_group_row'] = resultTB4['fs_group_row'].fillna('n/a group')
                    resultTB4['fs_group_name'] = resultTB4['fs_group_name'].fillna('n/a group')
                    resultTB4['account_type'] = resultTB4['account_type'].fillna('n/a group')
                    resultTB4['account_subtype'] = resultTB4['account_subtype'].fillna('n/a group')
                    resultTB5 = resultTB4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','fs_group_row','fs_group_name'])
                    resultTB6 = resultTB5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultTB6 = "Null"

                if not df_interco.empty:
                    resultInterco = pd.merge(df_interco, df_company, on=['company_code'], how='left')
                    resultInterco2 = pd.merge(resultInterco, df_coa, on=['account_code','company_code'], how='left')
                    resultInterco3 = pd.merge(resultInterco2, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultInterco4 = resultInterco3.drop(columns=['period_code','account_code', 'account_name','company_type'])
                    resultInterco4['wk_group_row'] = resultInterco4['wk_group_row'].fillna('n/a group')
                    resultInterco4['wk_group_name'] = resultInterco4['wk_group_name'].fillna('n/a group')
                    resultInterco4['fs_group_row'] = resultInterco4['fs_group_row'].fillna('n/a group')
                    resultInterco4['fs_group_name'] = resultInterco4['fs_group_name'].fillna('n/a group')
                    resultInterco4['account_type'] = resultInterco4['account_type'].fillna('n/a group')
                    resultInterco4['account_subtype'] = resultInterco4['account_subtype'].fillna('n/a group')
                    resultInterco4['rpt_amount'] = resultInterco4['rpt_amount'].fillna('0.00')
                    resultInterco5 = resultInterco4.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','fs_group_row','fs_group_name'])
                    resultInterco6 = resultInterco5.apply(pd.to_numeric, errors='ignore')
                else:
                    resultInterco6 = "Null"

                if not df_journalHeader.empty:
                    resultJV = pd.merge(df_journalHeader, df_journal, on=['journal_no'], how='left')
                    resultJV2 = pd.merge(resultJV, df_company, on=['company_code'], how='left')
                    resultJV3 = pd.merge(resultJV2, df_coa, on=['account_code','company_code'], how='left')
                    resultJV4 = pd.merge(resultJV3, df_fsgroup, left_on=  ['parent_company', 'wk_group_row'],right_on= ['company_code', 'wk_group_row'], how='left')
                    resultJV5 = resultJV4.drop(columns=['period_code','account_code', 'journal_no','account_name','company_type'])
                    resultJV5['wk_group_row'] = resultJV5['wk_group_row'].fillna('n/a group')
                    resultJV5['wk_group_name'] = resultJV5['wk_group_name'].fillna('n/a group')
                    resultJV5['fs_group_row'] = resultJV5['fs_group_row'].fillna('n/a group')
                    resultJV5['fs_group_name'] = resultJV5['fs_group_name'].fillna('n/a group')
                    resultJV5['account_type'] = resultJV5['account_type'].fillna('n/a group')
                    resultJV5['account_subtype'] = resultJV5['account_subtype'].fillna('n/a group')
                    resultJV5['journal_amount'] = resultJV5['journal_amount'].fillna('0.00')
                    ### เเยก Reclass กับ TakeEq
                    resultJV5['reclass_amount'] = resultJV5.loc[resultJV5['journal_type']== 'Reclassify', 'journal_amount']
                    resultJV5['reclass_amount'] = resultJV5['reclass_amount'].fillna('0.00')
                    resultJV5['takeEq_amount'] = resultJV5.loc[resultJV5['journal_type']== 'TakeEq', 'journal_amount']
                    resultJV5['takeEq_amount'] = resultJV5['takeEq_amount'].fillna('0.00')
                    resultJV6 = resultJV5.set_index(['account_type', 'account_subtype', 'wk_group_row','wk_group_name','fs_group_row','fs_group_name'])
                    resultJV7 = resultJV6.apply(pd.to_numeric, errors='ignore')
                else:
                    resultJV7 = "Null"

                if not TB.empty and not df_interco.empty and not df_journalHeader.empty :
                    result0 = resultTB6.append(resultInterco6, sort=False)
                    result = result0.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype','fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] = result2['Total TB'] + result2['rpt_amount'] + result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB','reclass_amount']].sum(axis=1)
                    result3['SeparateFS'].fillna(0, inplace=True)
                
                elif not TB.empty and not df_interco.empty :
                    result = resultTB6.append(resultInterco6, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] = result2['Total TB'] + result2['rpt_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB']].sum(axis=1)
                    result3['SeparateFS'].fillna(0, inplace=True)
                    
                elif not df_interco.empty and not df_journalHeader.empty :
                    result = resultInterco6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype','fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] = result2['rpt_amount'] + + result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB','reclass_amount']].sum(axis=1)
                    result3['SeparateFS'].fillna(0, inplace=True)

                elif not TB.empty and not df_journalHeader.empty :
                    result = resultTB6.append(resultJV7, sort=False)
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] = result2['Total TB'] + result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB','reclass_amount']].sum(axis=1)
                    result3['SeparateFS'].fillna(0, inplace=True)

                elif not TB.empty :
                    result = resultTB6
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] = result2['Total TB']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = result3.loc[result3['company_code_x']== str(user_com_code),['Total TB']].sum(axis=1)
                    result3['SeparateFS'].fillna(0, inplace=True)

                elif not df_interco.empty :
                    result = resultInterco6
                    result2 = result.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] =  result2['rpt_amount'] 
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = "0"

                elif not df_journalHeader.empty :
                    result = resultJV7
                    result2 = result.groupby(['account_type', 'account_subtype','fs_group_row','fs_group_name','company_code_x'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                    result2['ConsolidatedFS'] = result2['reclass_amount'] + result2['takeEq_amount']
                    ###### Separate FS ###### 
                    result3 = result2
                    result3['SeparateFS'] = result3.loc[result3['company_code_x']== str(user_com_code),['reclass_amount']].sum(axis=1)
                    result3['SeparateFS'].fillna(0, inplace=True)
                else:
                    messages.warning(request ,'No data found!')

                result4 = result3[['account_type', 'account_subtype','fs_group_row','fs_group_name','SeparateFS','ConsolidatedFS']]
                result4.set_index(['account_type', 'account_subtype', 'fs_group_row','fs_group_name'])
                result5 = result4.loc[result4['account_type'].isin(['รายได้','ค่าใช้จ่าย'])]
                result6 = result5.groupby(['account_type', 'account_subtype', 'fs_group_row','fs_group_name'], dropna=False).sum().reset_index().sort_values('fs_group_row', ascending=True)
                result6['SeparateFS'] = np.where(result6.all, result6.SeparateFS * -1, result6.SeparateFS) 
                result6['ConsolidatedFS'] = np.where(result6.all, result6.ConsolidatedFS * -1, result6.ConsolidatedFS)
                # result6['SeparateFS'] = np.where(result6.account_type == 'รายได้', result6.SeparateFS * -1, result6.SeparateFS)   
                result6.loc["Total"] = result6.sum(numeric_only=True, axis=0)
                result6.append(result5.sum(numeric_only=True),ignore_index=True)
                result6[['fs_group_name']] = result6[['fs_group_name']].fillna(value='Total')
                result6.fillna('', inplace=True)
                # df.eval('C = A + B', inplace=True)
                Colname = {'account_type':'Account type', 'account_subtype':'Account subtype', 'fs_group_row':'FS group row','fs_group_name':'FS group name','SeparateFS':'Separate FS','ConsolidatedFS':'Consolidated FS'}
                result6.rename(columns=Colname , inplace= True)
                
                # HTML
                final_result = result6.to_html(index=False,classes='table table-bordered table-sm ' , header = "true", justify = "center") 
                
                # Create a Pandas Excel writer using XlsxWriter as the engine.
                # response = HttpResponse(content_type='application/ms-excel')
                # response['Content-Disposition'] = 'attachment; filename="PL_Statement.xlsx"'
                # writer = pd.ExcelWriter('PL_Statement.xlsx', engine='xlsxwriter')
                # result6.to_excel(writer, sheet_name='Sheet1', index=False)
                # writer.save(response)
                # return response           

        return render(request, 'Report_pl.html',{'form':form,'final_result':final_result })
    else:
        form = WorkingForm()
    return render(request,'Report_pl.html',{'form':form})

############# Admin Report #################
# @user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='Login')
def SubscriptionReport(request):
    if request.method == "POST":
        form = SubscriptionForm(request.POST)
        CompanyCode = request.POST['CompanyCodeFilter']
        CompanyName = request.POST['CompanyNameFilter']
        PlanCode = request.POST['PlanCodeFilter']
        if form.is_valid():
            pd.options.display.float_format = "{:,.2f}".format
            # qs = Subscription_Master.objects.filter(Q(company_code = CompanyCode)|Q(company_name = CompanyName)|Q(plan_code = PlanCode)).values()
            qs = Subscription_Master.objects.all().values()
            df_sub = pd.DataFrame(list(qs))
            df_company = pd.DataFrame(list(Company_Master.objects.values('company_code','company_name','parent_company')))
            df_plan = pd.DataFrame(list(Plan_Master.objects.values('plan_code','plan_description','plan_price')))
            # qs = Interco_transactions.objects.filter(Q(company_code__in = company_list)&Q(period_code=period))  #ใช้ & เป็นจริงทุกเงื่อนไข ใช้ | เป็นจริงเงื่อนไขใดก็ได้
            if not qs:
                messages.warning(request ,'No data found!')
                return redirect(reverse('SubscriptionReport'))
            result = pd.merge(df_sub, df_company, on=['company_code'], how='left')
            result2 = pd.merge(result, df_plan, on=['plan_code'], how='left')
            result3 = result2[['company_code', 'company_name','plan_code','plan_description','plan_price','start_date','end_date']]
            
            if len(request.POST['CompanyCodeFilter'])>1 or len(request.POST['CompanyNameFilter'])>1 or len(request.POST['PlanCodeFilter'])>1  :
                result3.query(('company_code == @CompanyCode | company_name == @CompanyName | plan_code == @PlanCode') , inplace = True)
            
            Colname = {'company_code':'Company code', 'company_name':'Company name', 'plan_code':'Plan code','plan_description':'Plan Description','plan_price':'Plan price','start_date':'Start date','end_date':'End date'}
            result3.rename(columns=Colname , inplace= True)

            final_result = result3.to_html(index=False, classes='table table-bordered table-sm ' , header = "true", justify = "center")
        return render(request, 'SubscriptionReport.html', {'form': form,'final_result':final_result})
    else:
        form = SubscriptionForm()
    return render(request, 'SubscriptionReport.html', {'form': form})

# @user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='Login')
def CompanyMemberReport(request):
    if request.method == "POST":
        form = CompanyMemberForm(request.POST)
        CompanyCode = request.POST['CompanyCodeFilter']
        CompanyName = request.POST['CompanyNameFilter']
        ParentCompany = request.POST['ParentCompanyFilter']
        if form.is_valid():
            pd.options.display.float_format = "{:,.2f}".format
            # qs = Subscription_Master.objects.filter(Q(company_code = CompanyCode)|Q(company_name = CompanyName)|Q(plan_code = PlanCode)).values()
            qs = Company_Master.objects.all().values()
            if not qs:
                messages.warning(request ,'No data found!')
                return redirect(reverse('CompanyMemberReport'))
            df_com = pd.DataFrame(list(qs))
            df_com2 = df_com[['company_code','company_name']]
            df_com2 = df_com2.rename(columns={'company_code':'parent_company',"company_name":"parent_company_name"})
            df_com3 = pd.merge(df_com,df_com2,on=['parent_company'],how="left")
            df_com3['count'] = df_com3.groupby('parent_company')['parent_company'].transform('count')

            result = df_com3[['parent_company','parent_company_name','company_code', 'company_name','company_type','country','currency','company_est_date','company_start_date','company_end_date','count']]
                        
            if len(request.POST['CompanyCodeFilter'])>1 or len(request.POST['CompanyNameFilter'])>1 or len(request.POST['ParentCompanyFilter'])>1  :
                result.query(('company_code == @CompanyCode | company_name == @CompanyName | parent_company == @ParentCompany') , inplace = True)
            
            Colname = {'company_code':'Company code', 'company_name':'Company name', 'company_type':'company type','parent_company':'Parent company code','parent_company_name':'Parent company name','country':'Country','currency':'Currency','company_est_date':'Established date','company_start_date':'Start date','company_end_date':'End date','count':'Company count'}
            result.rename(columns=Colname , inplace= True)

            final_result = result.to_html(index=False, classes='table table-bordered table-sm ' , header = "true", justify = "center")
        return render(request, 'CompanyMemberReport.html', {'form': form,'final_result':final_result})
    else:
        form = CompanyMemberForm()
    return render(request, 'CompanyMemberReport.html', {'form': form})

# @user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='Login')
def PlanPriceReport(request):
    data = Plan_Master.objects.all()
    return render(request, 'PlanPriceReport.html', {'data': data,  })

# @user_passes_test(lambda u: u.is_superuser)
@login_required(login_url='Login')
def UserReport(request):
    if request.method == "POST":
        form = UserAdminForm(request.POST)
        username = request.POST['UsernameFilter']
        FirstName = request.POST['FirstNameFilter']
        LastName = request.POST['LastNameFilter']
        company = request.POST['CompanyCodeFilter']
        if form.is_valid():
            pd.options.display.float_format = "{:,.2f}".format
            # qs = Subscription_Master.objects.filter(Q(company_code = CompanyCode)|Q(company_name = CompanyName)|Q(plan_code = PlanCode)).values()
            qs = MyUserModel.objects.all().values()
            df_user = pd.DataFrame(list(qs))
            df_usergroup = pd.DataFrame(list(MyUserModel.objects.all().values('username','groups')))
            df_group = pd.DataFrame(list(Group.objects.all().values()))
            df_group = df_group.rename(columns={'id':'groups','name':'Group name'})
            df_company = pd.DataFrame(list(Company_Master.objects.values('id','company_code','company_name')))
            df_company = df_company.rename(columns={'id':'company_code_id'})
            result = pd.merge(df_user, df_usergroup, on=['username'], how='left')
            result2 = pd.merge(result, df_group, on=['groups'], how='left')
            result3 = pd.merge(result2, df_company, on=['company_code_id'], how='left')
            result4 = result3[['username', 'first_name','last_name','company_code','company_name','Group name','is_superuser','is_staff','is_active','date_joined','last_login']]
            result4['date_joined'] = result4['date_joined'].dt.strftime('%Y-%m-%d %H:%M:%S')
            result4['last_login'] = result4['last_login'].dt.strftime('%Y-%m-%d %H:%M:%S')
            if len(request.POST['UsernameFilter'])>1 or len(request.POST['FirstNameFilter'])>1 or len(request.POST['LastNameFilter'])>1 or len(request.POST['CompanyCodeFilter'])>1 :
                result4.query(('username == @username | first_name == @FirstName | last_name == @LastName| company_code == @company') , inplace = True)
            
            Colname = {'username':'Username', 'first_name':'First name','last_name':'Last name','company_code':'Company code','company_name':'Company name','is_superuser':'Superuser','is_staff':'Staff','is_active':'Active','date_joined':'Date joined','last_login':'Last login'}
            result4.rename(columns=Colname , inplace= True)
        
            final_result = result4.to_html(index=False, classes='table table-bordered table-sm ' , header = "true", justify = "center")
        return render(request, 'UserReport.html', {'form': form,'final_result':final_result})
    else:
        form = UserAdminForm()
    return render(request, 'UserReport.html', {'form': form})

@login_required(login_url='Login')
def AdminLogReport(request):
    if request.method == "POST":
        form = AdminLogForm(request.POST)
        username = request.POST['UsernameFilter']
        date = request.POST['DateFilter']
        if form.is_valid():
            pd.options.display.float_format = "{:,.2f}".format
            df_log = pd.DataFrame(list(LogEntry.objects.all().values()))
            df_content = pd.DataFrame(list(ContentType.objects.all().values()))
            df_content = df_content.rename(columns={'id':'content_type_id'})
            df_user = pd.DataFrame(list(MyUserModel.objects.all().values('id','username','first_name','last_name')))
            df_user = df_user.rename(columns={'id':'user_id'})

            result = pd.merge(df_log, df_content, on=['content_type_id'], how='left')
            result1 = pd.merge(result, df_user, on=['user_id'], how='left')
            result1['action_date'] = result1['action_time']
            result2 = result1[['id','content_type_id','app_label','model','object_id','object_repr','action_flag','change_message','user_id','username', 'first_name','last_name','action_date','action_time']]
            result2['action_date'] = result2['action_date'].dt.strftime('%Y-%m-%d')
            result2['action_time'] = result2['action_time'].dt.strftime('%H:%M:%S')

            if len(request.POST['UsernameFilter'])>1  or len(request.POST['DateFilter'])>1  :
                result2.query(('username == @username  | action_date == @date') , inplace = True)
            
            Colname = {'content_type_id':'Content type id','app_label':'App label','model':'Model','object_id':'Object id','object_repr':'Object repr','action_flag':'Action flag',
                'change_message':'Change message','user_id':'User id','username':'Username', 'first_name':'First name','last_name':'Last name','action_date':'Action date','action_time':'Action time'}
            result2.rename(columns=Colname , inplace= True)
        
            final_result = result2.to_html(index=False, classes='table table-bordered table-sm ' , header = "true", justify = "center")
        return render(request, 'AdminLogReport.html', {'form': form,'final_result':final_result})
    else:
        form = AdminLogForm()
    return render(request, 'AdminLogReport.html', {'form': form})

