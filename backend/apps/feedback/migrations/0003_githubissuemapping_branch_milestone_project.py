from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("feedback", "0002_githubissuemapping_api_error_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="githubissuemapping",
            name="branch_name",
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name="githubissuemapping",
            name="milestone",
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name="githubissuemapping",
            name="project_node_id",
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
