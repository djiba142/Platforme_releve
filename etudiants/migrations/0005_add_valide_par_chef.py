from django.db import migrations, models
import django.utils.timezone

class Migration(migrations.Migration):

    dependencies = [
        ('etudiants', '0004_alter_profiladmin_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='etudiant',
            name='valide_par_chef',
            field=models.BooleanField(default=False, verbose_name='Pré-validé par chef département'),
        ),
        migrations.AddField(
            model_name='etudiant',
            name='date_inscription',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
