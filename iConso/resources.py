from import_export import widgets,fields, resources
from import_export.widgets import ForeignKeyWidget
from .models import Trial_balance ,  Interco_transactions,Company_Master,Periods,COA_Master

class TrialResources(resources.ModelResource):
    # company_code = fields.Field(
    #     column_name='company_code',
    #     attribute='company_code',
    #     widget=ForeignKeyWidget(Company_Master, 'company_code'))
    # period_code = fields.Field(
    #     column_name='period_code',
    #     attribute='period_code',
    #     widget=ForeignKeyWidget(Periods, 'period_code')) #(model,'field')
    # account_code = fields.Field(
    #     column_name='account_code',
    #     attribute='account_code',
    #     widget=ForeignKeyWidget(COA_Master, 'account_code')) #(model,'field')

    class Meta:
        model = Trial_balance
        exclude = ('id',)
        report_skipped = True
        import_id_fields = ['company_code','period_code','account_code','tb_amount']
        fields = ('company_code','period_code','account_code','tb_amount')
    class AccountNameForeignKeyWidget(ForeignKeyWidget):
        def get_queryset(self, value, row):
            return self.model.objects.filter(
                account_code__iexact=row["account_code"],
                account_name__iexact=row["account_name"],
                fs_group_code__iexact=row["fs_group_code"]
            )

class IntercoResources(resources.ModelResource):
    period_code = fields.Field(
        column_name='period_code',
        attribute='period_code',
        widget=ForeignKeyWidget(Periods, 'period_code')) #(model,'field')
    company_code = fields.Field(
        column_name='company_code',
        attribute='company_code',
        widget=ForeignKeyWidget(Company_Master, 'company_code'))
    account_code = fields.Field(
        column_name='account_code',
        attribute='account_code',
        widget=ForeignKeyWidget(COA_Master, 'account_code')) #(model,'field')
    class Meta:
        model = Interco_transactions
        exclude = ('id',)


