import re
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db.models import Model

EMAIL_REGEX = re.compile(
    r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+"
    r'(\.[-!#$%&\'*+/=?^_`{}|~0-9A-Z]+)*'
    r'@'
    r'([A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+'
    r'[A-Z]{2,6}\.?$)',
    re.IGNORECASE,
)

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")

def validate_email_format(value: str) -> None:
    if not EMAIL_REGEX.match(value):
        raise ValidationError(
            _("Enter a valid email address."),
            params={"value": value},
        )

def validate_phone_number(value: str) -> None:
    if not PHONE_REGEX.match(value):
        raise ValidationError(
            _("Enter a valid international phone number."),
            params={"value": value},
        )

def validate_positive_decimal(value, field_name="price") -> Decimal:
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, TypeError):
        raise ValidationError(
            _(f"{field_name} must be a numeric value."),
            params={"value": value},
        )
    if decimal_value <= 0:
        raise ValidationError(
            _("%(field)s must be greater than zero."),
            params={"field": field_name},
        )
    return decimal_value

def validate_slug_unique(instance: Model, slug_field="slug") -> None:
    queryset = instance.__class__.objects.filter(**{slug_field: getattr(instance, slug_field)})
    if instance.pk:
        queryset = queryset.exclude(pk=instance.pk)
    if queryset.exists():
        raise ValidationError(
            _("%(field)s must be unique."),
            params={"field": slug_field},
        )