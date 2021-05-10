from django.db import models
from django.contrib.auth.models import User, Group, AbstractBaseUser,AbstractUser,BaseUserManager,PermissionsMixin
from django.db.models.signals import post_save
from django.db.models import Q, Count, Sum, Max, Min
from django.dispatch import receiver
from django.conf import settings
from django.utils import timezone
import pytz
import datetime
from django_pandas.managers import DataFrameManager
from django.core.validators import MaxValueValidator, MinValueValidator

# class UserManager(BaseUserManager):
#     use_in_migrations = True

#     def _create_user(self, username, email, company_code, password, **extra_fields):
#         values = [email, company_code]
#         field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
#         for field_name, value in field_value_map.items():
#             if not value:
#                 raise ValueError('The {} value must be set'.format(field_name))

#         email = self.normalize_email(email)
#         user = self.model(
#             email=email,
#             company_code=company_code,
#             **extra_fields
#         )
#         user.set_password(password)
#         user.save(using=self._db)
#         return user

#     def create_user(self, email, company_code, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', False)
#         extra_fields.setdefault('is_superuser', False)
#         return self._create_user(email, company_code, password, **extra_fields)

#     def create_superuser(self, email, company_code=None, password=None, **extra_fields):
#         extra_fields.setdefault('is_staff', True)
#         extra_fields.setdefault('is_superuser', True)

#         if extra_fields.get('is_staff') is not True:
#             raise ValueError('Superuser must have is_staff=True.')
#         if extra_fields.get('is_superuser') is not True:
#             raise ValueError('Superuser must have is_superuser=True.')

#         return self._create_user(email,company_code, password, **extra_fields)

class MyUserModel(AbstractUser):
    email = models.EmailField(unique=True)
    company_code = models.ForeignKey('Company_Master', null=True, on_delete=models.CASCADE, related_name='MyUser')
    # objects = UserManager()
    # USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['email']
    def __str__(self):
        return self.email

class Company_Master(models.Model):
    company_code = models.CharField(max_length=5,unique=True)
    company_name = models.CharField(max_length=100,unique=True)
    company_type = models.CharField(max_length=100)
    # company_type = models.CharField(        
    #     choices=[('Parent', 'Parent'),('Subsidiary', 'Subsidiary'), ('Associate', 'Associate'),('Investment', 'Investment')],
    #     max_length=100)
    parent_company = models.CharField(max_length=5,null=True, blank=True)
    company_est_date = models.DateField()
    country = models.CharField(max_length=100,default='Thailand')
    currency = models.CharField(max_length=3,default='THB')
    consolidation_rate = models.FloatField(default='100')
    company_start_date = models.DateField()
    company_end_date = models.DateField(null=True, blank=True)
    company_date_create = models.DateTimeField(auto_now_add=True)
    company_date_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.company_code

class Plan_Master(models.Model):
    plan_code = models.CharField(max_length=5,unique=True)
    plan_description = models.CharField(max_length=100,unique=True)
    plan_price = models.FloatField(max_length=15)
    plan_date_create = models.DateTimeField(auto_now_add=True)
    plan_date_update = models.DateTimeField(auto_now=True)

class Subscription_Master(models.Model):
    company_code = models.CharField(max_length=5,unique=True)
    plan_code = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    date_create = models.DateTimeField(auto_now_add=True)
    date_update = models.DateTimeField(auto_now=True)

class Periods(models.Model):
    # company = models.ForeignKey('Company_Master', on_delete=models.CASCADE,related_name='Periods',)
    company_code = models.CharField(max_length=5,null=True, blank=True)
    period_code = models.CharField(max_length=7)
    period_description = models.CharField(max_length=100)
    period_date_from = models.DateField()
    period_date_to = models.DateField()
    period_status = models.CharField(        
        choices=[('Open', 'Open'),('Closed', 'Closed'), ('Never Open', 'Never Open')],
        max_length=50,default='Never Open'
    )
    period_create = models.DateTimeField(auto_now_add=True)
    period_update = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company_code', 'period_code'], name='Aconstraint'),
            models.UniqueConstraint(
                fields=['company_code', 'period_status'], condition=Q(period_status='Open') , name='Bconstraint'),
        ]
        # unique_together = ('company', 'period_code')
    def __str__(self):
        return self.period_code

class COA_Master(models.Model):
    # company = models.ForeignKey('Company_Master', on_delete=models.CASCADE,related_name='COA_Master',)
    company_code = models.CharField(max_length=5,null=True, blank=True)
    account_code = models.CharField(max_length=15)
    account_name = models.CharField(max_length=255)
    fs_group = models.ForeignKey('FS_grouping_Master', on_delete=models.CASCADE,related_name='COA_Master',)
    wk_group_row = models.CharField(max_length=10,null=True, blank=True)
    account_date_create = models.DateTimeField(auto_now_add=True)
    account_date_update = models.DateTimeField(auto_now=True)
    objects = DataFrameManager()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company_code', 'account_code'], name='COAconstraint')]
    def __str__(self):
        return self.account_code

class FS_grouping_Master(models.Model):
    # company = models.ForeignKey('Company_Master', on_delete=models.CASCADE,related_name='FS_grouping_Master',)
    company_code = models.CharField(max_length=5,null=True, blank=True)
    fs_group_row = models.CharField(max_length=10)
    fs_group_name = models.CharField(max_length=255)
    wk_group_row = models.CharField(max_length=10)
    wk_group_name = models.CharField(max_length=255)
    account_type = models.CharField(
        max_length=255,
        choices=[('สินทรัพย์', 'สินทรัพย์'),('หนี้สิน', 'หนี้สิน'),('ส่วนของผู้ถือหุ้น', 'ส่วนของผู้ถือหุ้น'),('รายได้', 'รายได้'),('ค่าใช้จ่าย', 'ค่าใช้จ่าย')],
        )
    account_subtype = models.CharField(
        max_length=255,
        choices=[('สินทรัพย์', 'สินทรัพย์'),('สินทรัพย์หมุนเวียน', 'สินทรัพย์หมุนเวียน'),('สินทรัพย์ไม่หมุนเวียน', 'สินทรัพย์ไม่หมุนเวียน'),
        ('หนี้สิน', 'หนี้สิน'),('หนี้สินหมุนเวียน', 'หนี้สินหมุนเวียน'),('หนี้สินไม่หมุนเวียน', 'หนี้สินไม่หมุนเวียน'),
        ('ส่วนของผู้ถือหุ้น', 'ส่วนของผู้ถือหุ้น'),('ทุนเรือนหุ้น', 'ทุนเรือนหุ้น'),('ทุนจดทะเบียน', 'ทุนจดทะเบียน'),('ทุนที่ออกและชำระแล้ว', 'ทุนที่ออกและชำระแล้ว'),
        ('ส่วนเกิน (ต่ำกว่า) มูลค่าหุ้น', 'ส่วนเกิน (ต่ำกว่า) มูลค่าหุ้น'),('กำไร (ขาดทุน) สะสม', 'กำไร (ขาดทุน) สะสม'),('กำไร (ขาดทุน) สะสม-จัดสรรแล้ว', 'กำไร (ขาดทุน) สะสม-จัดสรรแล้ว'),('หุ้นกู้ที่มีลักษณะคล้ายทุน', 'หุ้นกู้ที่มีลักษณะคล้ายทุน'),
        ('รายได้', 'รายได้'),('ต้นทุน', 'ต้นทุน'),('ค่าใช้จ่าย', 'ค่าใช้จ่าย'),('กำไร (ขาดทุน) เบ็ดเสร็จอื่น', 'กำไร (ขาดทุน) เบ็ดเสร็จอื่น'),
        ],
        )
    # fs_parent_group_code = models.CharField(max_length=10)
    # fs_level = models.CharField(
    #     max_length=10,
    #     choices=[('Level 1', 'Level 1'),('Level 2', 'Level 2'),('Level 3', 'Level 3'),('Level 4', 'Level 4'),('Level 5', 'Level 5')],
    #     )
    # fs_show_status = models.CharField(
    #     max_length=10,
    #     choices=[('Show', 'Show'),('No show', 'No show')],
    #     default='Show'
    #     )
    fs_date_create = models.DateTimeField(auto_now_add=True)
    fs_date_update = models.DateTimeField(auto_now=True)
    objects = DataFrameManager()
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['company_code', 'wk_group_row'], name='Groupconstraint')]
    def __str__(self):
        return self.wk_group_row
    def __unicode__(self):
        return '%s' % self.wk_group_row

class Trial_balance(models.Model):
    company_code = models.CharField(max_length=5)
    period_code = models.CharField(max_length=7)  
    account_code = models.CharField(max_length=15)  
    tb_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
    tb_date_create = models.DateTimeField(auto_now=True , null=True, blank=True )
    tb_file_name = models.CharField(max_length=255 , null=True, blank=True)

class Interco_transactions(models.Model):
    company_code = models.CharField(max_length=5)
    period_code = models.CharField(max_length=7)  
    rpt_interco_code = models.CharField(max_length=5)
    account_code = models.CharField(max_length=15)
    rpt_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
    rpt_date_create = models.DateTimeField(auto_now=True , null=True, blank=True)
    rpt_file_name = models.CharField(max_length=255 , null=True, blank=True)
    objects = DataFrameManager()

# def increment_Journal_no():
#     last_journal = JournalHeader.objects.all().order_by('journal_no').last()
#     if not last_journal:
#         return 'JV_'+ '00001'
#     journal_no = last_journal.journal_no
#     journal_int = int(journal_no.split('JV_')[-1])
#     new_journal_int = journal_int + 1
#     new_journal_no = str(new_journal_int)
#     return new_journal_no

class JournalHeader(models.Model):
    journal_no = models.CharField(max_length=15, null=True, blank=True) #default=increment_Journal_no,
    period_code = models.CharField(max_length=7)
    Parent_company_code = models.CharField(max_length=5,null=True, blank=True)
    company_code = models.CharField(max_length=5,null=True, blank=True)
    journal_type = models.CharField(max_length=255, null=True, blank=True)
    journal_description = models.CharField(max_length=1000)
    journal_date_create = models.DateTimeField(auto_now_add=True)
    journal_date_update = models.DateTimeField(auto_now=True)
    objects = DataFrameManager()
    def __str__(self):
        return str(self.id)
    def __int__(self):
        return self.id
    def __unicode__(self):
        return u"%s's order" % self.id

class Journals(models.Model):
    JournalHeader = models.ForeignKey('JournalHeader', on_delete=models.CASCADE,related_name='Journals',)
    journal_no = models.CharField(max_length=15, null=True, blank=True)
    company_code = models.CharField(max_length=5,null=True, blank=True)
    rpt_interco_code = models.CharField(max_length=5, null=True, blank=True)
    account_code = models.CharField(max_length=15)
    account_name = models.CharField(max_length=255)
    debit = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True, validators=[MinValueValidator(0)])
    credit = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True, validators=[MinValueValidator(0)])
    journal_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
    objects = DataFrameManager()
    def save(self, *args, **kwargs):
        if self.debit is None:
            self.debit = 0
        if self.credit is None:
            self.credit = 0
        self.journal_amount = self.debit-self.credit
        return super().save(*args, **kwargs)

# class Conso(models.Model):
#     period_code = models.CharField(max_length=7)
#     data_source = models.CharField(max_length=10,null=True, blank=True)
#     company_code = models.CharField(max_length=5,null=True, blank=True)
#     account_code = models.CharField(max_length=15)
#     account_name = models.CharField(max_length=255)
#     fs_group_row = models.CharField(max_length=10)
#     fs_group_name = models.CharField(max_length=255)
#     wk_group_row = models.CharField(max_length=10)
#     wk_group_name = models.CharField(max_length=255)
#     tb_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
#     journal_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
#     rpt_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
#     conso_amount = models.DecimalField( max_digits = 15, decimal_places = 2 , null=True, blank=True)
