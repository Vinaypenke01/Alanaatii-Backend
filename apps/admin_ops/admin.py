from django.contrib import admin
from .models import PricingDayRule, PincodeRule, MandatoryQuestion, Coupon, SiteSettings, SupportMessage

admin.site.register(PricingDayRule)
admin.site.register(PincodeRule)
admin.site.register(MandatoryQuestion)
admin.site.register(Coupon)
admin.site.register(SiteSettings)
admin.site.register(SupportMessage)
