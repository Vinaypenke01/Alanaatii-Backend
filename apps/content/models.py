"""Content models — Reviews, FAQ, SiteContentSteps."""
from django.db import models
from django.utils import timezone


class Review(models.Model):
    order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    customer_name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5)
    content = models.TextField()
    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.customer_name} – {self.rating}★'


class FAQ(models.Model):
    question = models.TextField()
    answer = models.TextField()
    category = models.CharField(max_length=50, default='General')
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    created_by = models.ForeignKey('accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'faq'
        ordering = ['category', 'display_order']

    def __str__(self):
        return self.question[:80]


class SiteContentStep(models.Model):
    step_num = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=100)
    description = models.TextField()
    icon_slug = models.CharField(max_length=50)
    created_by = models.ForeignKey('accounts.Admin', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'site_content_steps'
        ordering = ['step_num']

    def __str__(self):
        return f'Step {self.step_num}: {self.title}'
