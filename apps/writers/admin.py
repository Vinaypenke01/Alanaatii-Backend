from django.contrib import admin
from .models import WriterAssignment, WriterDraft, Payout

admin.site.register(WriterAssignment)
admin.site.register(WriterDraft)
admin.site.register(Payout)
