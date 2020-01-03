from django.apps import apps
from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _
from .models import FCMDevice
from .settings import FCM_DJANGO_SETTINGS as SETTINGS

User = apps.get_model(*SETTINGS["USER_MODEL"].split("."))


class DeviceAdmin(admin.ModelAdmin):
    list_display = ("__str__", "device_id", "name", "type", "user", "active",
                    "date_created")
    list_filter = ("active",)
    actions = ("send_message", "send_bulk_message", "send_data_message",
               "send_bulk_data_message", "enable", "disable")
    raw_id_fields = ("user",)
    list_select_related = ("user",)

    def get_search_fields(self, request):
        if hasattr(User, "USERNAME_FIELD"):
            return ("name", "device_id", "user__%s" % (User.USERNAME_FIELD))
        else:
            return ("name", "device_id")

    def send_messages(self, request, queryset, bulk=False, data=False):
        """
        Provides error handling for DeviceAdmin send_message and
        send_bulk_message methods.
        """
        ret = []
        errors = []
        total_failure = 0

        for device in queryset:
            if bulk:
                if data:
                    response = queryset.send_message(
                        data={"Nick": "Mario"}
                    )
                else:
                    response = queryset.send_message(
                        title="Test notification",
                        body="Test bulk notification"
                    )
            else:
                if data:
                    response = device.send_message(data={"Nick": "Mario"})
                else:
                    response = device.send_message(
                        title="Test notification",
                        body="Test single notification"
                    )
            if response:
                ret.append(response)

            failure = int(response['failure'])
            total_failure += failure
            errors.append(str(response))

            if bulk:
                break

        if ret:
            if errors:
                msg = _("Some messages were sent: %s" % (ret))
            else:
                msg = _("All messages were sent: %s" % (ret))
            self.message_user(request, msg)

        if total_failure > 0:
            self.message_user(
                request,
                _("Some messages failed to send. %d devices were marked as "
                  "inactive." % total_failure),
                level=messages.WARNING
            )

    def send_message(self, request, queryset):
        self.send_messages(request, queryset)

    send_message.short_description = _("Send test notification")

    def send_bulk_message(self, request, queryset):
        self.send_messages(request, queryset, True)

    send_bulk_message.short_description = _("Send test notification in bulk")

    def send_data_message(self, request, queryset):
        self.send_messages(request, queryset, False, True)

    send_data_message.short_description = _("Send test data message")

    def send_bulk_data_message(self, request, queryset):
        self.send_messages(request, queryset, True, True)

    send_bulk_data_message.short_description = _(
        "Send test data message in bulk")

    def enable(self, request, queryset):
        queryset.update(active=True)

    enable.short_description = _("Enable selected devices")

    def disable(self, request, queryset):
        queryset.update(active=False)

    disable.short_description = _("Disable selected devices")


admin.site.register(FCMDevice, DeviceAdmin)
