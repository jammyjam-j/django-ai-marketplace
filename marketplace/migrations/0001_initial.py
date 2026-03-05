from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name='ID'
                    )
                ),
                (
                    'name',
                    models.CharField(max_length=255)
                ),
                (
                    'description',
                    models.TextField(blank=True)
                ),
                (
                    'price',
                    models.DecimalField(
                        max_digits=10,
                        decimal_places=2,
                        default=0.00
                    )
                ),
                (
                    'category',
                    models.CharField(max_length=100)
                ),
                (
                    'created_at',
                    models.DateTimeField(auto_now_add=True)
                ),
                (
                    'updated_at',
                    models.DateTimeField(auto_now=True)
                ),
            ],
        ),
    ]