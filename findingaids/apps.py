from django.apps import AppConfig

# use django app config to customize display name
# used in django admin


class FindingAidsConfig(AppConfig):
    name = 'findingaids.fa'
    verbose_name = "Finding Aids"


class FindingAidsAdminConfig(AppConfig):
    name = 'findingaids.fa_admin'
    verbose_name = "Finding Aids Administration"
