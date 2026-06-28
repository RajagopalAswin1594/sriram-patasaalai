from django.contrib import admin

from apps.admissions.models import (
    AdmissionApplication,
    ApplicationDocument,
    ApplicationNotification,
    ApplicationPayment,
    ApplicationStatusHistory,
)


class ApplicationDocumentInline(admin.TabularInline):
    model = ApplicationDocument
    extra = 0


class ApplicationPaymentInline(admin.StackedInline):
    model = ApplicationPayment
    extra = 0


@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    list_display = ["application_number", "student_first_name", "branch", "status", "submitted_at", "created_at"]
    list_filter = ["status", "branch"]
    search_fields = ["application_number", "student_first_name", "parent_phone", "parent_email"]
    inlines = [ApplicationDocumentInline, ApplicationPaymentInline]
    readonly_fields = ["application_number", "access_token"]


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ["application", "from_status", "to_status", "changed_by", "occurred_at"]
    list_filter = ["to_status"]
    readonly_fields = [f.name for f in ApplicationStatusHistory._meta.fields]


@admin.register(ApplicationNotification)
class ApplicationNotificationAdmin(admin.ModelAdmin):
    list_display = ["application", "channel", "event_type", "status", "recipient", "sent_at"]
    list_filter = ["channel", "event_type", "status"]
    readonly_fields = [f.name for f in ApplicationNotification._meta.fields]
