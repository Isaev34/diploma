from django.contrib import admin



from .models import SupportMessage





class SupportReplyInline(admin.TabularInline):

    """Ответы поддержки к этому сообщению клиента."""



    model = SupportMessage

    fk_name = "reply_to"

    extra = 0

    fields = ("body", "created_at")

    readonly_fields = ("created_at",)

    verbose_name = "Ответ поддержки"

    verbose_name_plural = "Ответы поддержки (к этому вопросу клиента)"



    def get_queryset(self, request):

        return super().get_queryset(request).filter(is_staff_reply=True)





@admin.register(SupportMessage)

class SupportMessageAdmin(admin.ModelAdmin):

    list_display = ("id", "user", "order", "is_staff_reply", "reply_to", "body_short", "created_at")

    list_filter = ("is_staff_reply", "created_at")

    search_fields = ("body", "user__username", "user__email")

    raw_id_fields = ("user", "order")



    def get_readonly_fields(self, request, obj=None):

        base = ("created_at",)

        if obj and obj.is_staff_reply:

            return base + ("reply_to",)

        return base



    def get_fieldsets(self, request, obj=None):

        main_desc = (

            "Чтобы ответить клиенту: откройте именно сообщение клиента (тип «Клиент»), "

            "прокрутите вниз и добавьте строку в таблице «Ответы поддержки», сохраните страницу. "

            "Отдельно создавать новую запись «Чата» не нужно."

        )

        if obj and obj.is_staff_reply:

            return (

                (

                    None,

                    {"fields": ("user", "order", "is_staff_reply", "body")},

                ),

                ("Ответ на сообщение клиента", {"fields": ("reply_to",)}),

                ("Служебное", {"fields": ("created_at",)}),

            )

        return (

            (

                None,

                {

                    "fields": ("user", "order", "is_staff_reply", "body"),

                    "description": main_desc,

                },

            ),

            ("Служебное", {"fields": ("created_at",)}),

        )



    @admin.display(description="Текст")

    def body_short(self, obj):

        t = obj.body.replace("\n", " ")

        return (t[:80] + "…") if len(t) > 80 else t



    def get_queryset(self, request):

        return super().get_queryset(request).select_related("user", "order", "reply_to")



    def get_inlines(self, request, obj):

        if obj is None:

            return []

        if obj.is_staff_reply:

            return []

        return [SupportReplyInline]


