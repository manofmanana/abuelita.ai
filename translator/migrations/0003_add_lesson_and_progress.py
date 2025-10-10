# Generated migration to add Lesson and Progress models
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('translator', '0002_translation_delete_culturalphrase_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Lesson',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('title', models.CharField(max_length=200, blank=True)),
                ('content', models.TextField()),
                ('language', models.CharField(max_length=10, default='es')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='Progress',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, auto_created=True, verbose_name='ID')),
                ('user_id', models.CharField(max_length=100, default='local')),
                ('score', models.FloatField(default=0.0)),
                ('completed', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('lesson', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='progress', to='translator.lesson')),
            ],
        ),
    ]
