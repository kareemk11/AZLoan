from django.contrib import admin
from .models import User, Loan, LoanOffer, Payment

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'balance')  # include balance here

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('username', 'email', 'role', 'balance')

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = User
    list_display = ('username', 'email', 'role', 'is_staff', 'balance')

    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('role', 'balance')}),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('role', 'balance')}),
    )


admin.site.register(Loan)
admin.site.register(LoanOffer)
admin.site.register(Payment)