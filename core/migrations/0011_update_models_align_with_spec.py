# Generated manually to align models with specification requirements

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_evidencefact_evidenceinsight_evidencesource_and_more'),
    ]

    operations = [
        # Remove index that references is_active before removing the field
        migrations.RemoveIndex(
            model_name='project',
            name='core_projec_name_54f204_idx',
        ),
        
        # Update Project model fields
        migrations.RenameField(
            model_name='project',
            old_name='name',
            new_name='title',
        ),
        migrations.RemoveField(
            model_name='project',
            name='is_active',
        ),
        migrations.AlterField(
            model_name='project',
            name='status',
            field=models.CharField(
                choices=[
                    ('not_started', 'Not Started'),
                    ('in_progress', 'In Progress'),
                    ('completed', 'Completed'),
                    ('on_hold', 'On Hold')
                ],
                default='not_started',
                help_text='Current status of the project',
                max_length=20,
                verbose_name='Status'
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='description',
            field=models.TextField(
                blank=True,
                help_text='Longer text description (hypothesis or goal)',
                verbose_name='Description'
            ),
        ),
        migrations.AlterField(
            model_name='project',
            name='title',
            field=models.CharField(
                help_text='Short text title of the project',
                max_length=255,
                verbose_name='Title'
            ),
        ),
        
        # Update EvidenceSource model
        migrations.RenameField(
            model_name='evidencesource',
            old_name='name',
            new_name='title',
        ),
        migrations.RenameField(
            model_name='evidencesource',
            old_name='content',
            new_name='notes',
        ),
        migrations.RemoveField(
            model_name='evidencesource',
            name='project',
        ),
        migrations.RemoveField(
            model_name='evidencesource',
            name='upload_date',
        ),
        migrations.AddField(
            model_name='evidencesource',
            name='projects',
            field=models.ManyToManyField(
                blank=True,
                help_text='Projects this evidence source belongs to (optional)',
                related_name='evidence_sources',
                to='core.project',
                verbose_name='Projects'
            ),
        ),
        migrations.AlterField(
            model_name='evidencesource',
            name='type',
            field=models.CharField(
                choices=[
                    ('support_tickets', 'Support Tickets'),
                    ('interview', 'Interview'),
                    ('survey', 'Survey'),
                    ('analytics', 'Analytics'),
                    ('document', 'Document'),
                    ('video', 'Video'),
                    ('audio', 'Audio'),
                    ('text', 'Text'),
                    ('image', 'Image')
                ],
                help_text='Open text (e.g., Support Tickets, Interview, Survey, Analytics)',
                max_length=20,
                verbose_name='Type'
            ),
        ),
        migrations.AlterField(
            model_name='evidencesource',
            name='title',
            field=models.CharField(
                help_text='Smaller text area, always visible',
                max_length=255,
                verbose_name='Title'
            ),
        ),
        migrations.AlterField(
            model_name='evidencesource',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Detailed description, expandable by user',
                verbose_name='Notes'
            ),
        ),
        
        # Update EvidenceFact model
        migrations.RemoveField(
            model_name='evidencefact',
            name='project',
        ),
        migrations.RemoveField(
            model_name='evidencefact',
            name='content',
        ),
        migrations.RemoveField(
            model_name='evidencefact',
            name='extracted_at',
        ),
        migrations.AddField(
            model_name='evidencefact',
            name='projects',
            field=models.ManyToManyField(
                blank=True,
                help_text='Projects this observation belongs to (optional, can be multiple)',
                related_name='evidence_facts',
                to='core.project',
                verbose_name='Projects'
            ),
        ),
        migrations.AlterField(
            model_name='evidencefact',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Additional context; expandable',
                verbose_name='Notes'
            ),
        ),
        migrations.AlterField(
            model_name='evidencefact',
            name='participant',
            field=models.CharField(
                blank=True,
                help_text='Participant or speaker associated with this fact (optional)',
                max_length=255,
                verbose_name='Participant'
            ),
        ),
        migrations.AlterField(
            model_name='evidencefact',
            name='sentiment',
            field=models.CharField(
                blank=True,
                choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
                help_text='Sentiment analysis of the fact (optional)',
                max_length=20,
                null=True,
                verbose_name='Sentiment'
            ),
        ),
        migrations.AlterField(
            model_name='evidencefact',
            name='source',
            field=models.ForeignKey(
                help_text='Evidence source this fact was extracted from (required)',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='evidence_facts',
                to='core.evidencesource',
                verbose_name='Source'
            ),
        ),
        migrations.AlterField(
            model_name='evidencefact',
            name='tags_list',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Legacy list of tag names for this fact',
                verbose_name='Tags List'
            ),
        ),
        
        # Update EvidenceInsight model
        migrations.RemoveField(
            model_name='evidenceinsight',
            name='project',
        ),
        migrations.RemoveField(
            model_name='evidenceinsight',
            name='description',
        ),
        migrations.RenameField(
            model_name='evidenceinsight',
            old_name='related_facts',
            new_name='supporting_evidence',
        ),
        migrations.AddField(
            model_name='evidenceinsight',
            name='projects',
            field=models.ManyToManyField(
                blank=True,
                help_text='Projects this insight belongs to (optional, can be multiple)',
                related_name='evidence_insights',
                to='core.project',
                verbose_name='Projects'
            ),
        ),
        migrations.AddField(
            model_name='evidenceinsight',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Additional context; expandable',
                verbose_name='Notes'
            ),
        ),
        migrations.AddField(
            model_name='evidenceinsight',
            name='evidence_score',
            field=models.PositiveIntegerField(
                default=1,
                help_text='1-2: Limited Evidence, 3-5: Moderate Evidence, 6+: High Evidence',
                verbose_name='Evidence Score'
            ),
        ),
        migrations.AddField(
            model_name='evidenceinsight',
            name='sentiment',
            field=models.CharField(
                blank=True,
                choices=[('positive', 'Positive'), ('neutral', 'Neutral'), ('negative', 'Negative')],
                help_text='Sentiment analysis of the insight (optional)',
                max_length=20,
                null=True,
                verbose_name='Sentiment'
            ),
        ),
        migrations.AlterField(
            model_name='evidenceinsight',
            name='supporting_evidence',
            field=models.ManyToManyField(
                blank=True,
                help_text='Observations tied to this insight',
                related_name='insights',
                to='core.evidencefact',
                verbose_name='Supporting Evidence'
            ),
        ),
        migrations.AlterField(
            model_name='evidenceinsight',
            name='tags_list',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Legacy list of tag names for this insight',
                verbose_name='Tags List'
            ),
        ),
        
        # Update Recommendation model
        migrations.RemoveField(
            model_name='recommendation',
            name='project',
        ),
        migrations.RemoveField(
            model_name='recommendation',
            name='description',
        ),
        migrations.RenameField(
            model_name='recommendation',
            old_name='related_insights',
            new_name='supporting_evidence',
        ),
        migrations.AddField(
            model_name='recommendation',
            name='projects',
            field=models.ManyToManyField(
                blank=True,
                help_text='Projects this recommendation belongs to (optional, can be multiple)',
                related_name='recommendations',
                to='core.project',
                verbose_name='Projects'
            ),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='notes',
            field=models.TextField(
                blank=True,
                help_text='Additional context; expandable',
                verbose_name='Notes'
            ),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='type',
            field=models.CharField(
                choices=[('opportunity', 'Opportunity'), ('solution', 'Solution')],
                default='opportunity',
                help_text='Type of recommendation: Opportunity or Solution',
                max_length=20,
                verbose_name='Type'
            ),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='status',
            field=models.CharField(
                choices=[
                    ('not_started', 'Not Started'),
                    ('in_discovery', 'In Discovery'),
                    ('in_delivery', 'In Delivery'),
                    ('completed', 'Completed'),
                    ('wont_do', "Won't Do")
                ],
                default='not_started',
                help_text='Configurable checkbox status',
                max_length=20,
                verbose_name='Status'
            ),
        ),
        migrations.AddField(
            model_name='recommendation',
            name='evidence_score',
            field=models.PositiveIntegerField(
                default=1,
                help_text='Based on sum of associated insight evidence scores (1-2: Limited, 3-5: Moderate, 6+: High)',
                verbose_name='Evidence Score'
            ),
        ),
        migrations.AlterField(
            model_name='recommendation',
            name='supporting_evidence',
            field=models.ManyToManyField(
                blank=True,
                help_text='Insights tied to this recommendation',
                related_name='recommendations',
                to='core.evidenceinsight',
                verbose_name='Supporting Evidence'
            ),
        ),
        migrations.AlterField(
            model_name='recommendation',
            name='tags_list',
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Legacy list of tag names for this recommendation',
                verbose_name='Tags List'
            ),
        ),
        
        # Update EvidenceChunk model
        migrations.RemoveField(
            model_name='evidencechunk',
            name='project',
        ),
        migrations.AddField(
            model_name='evidencechunk',
            name='projects',
            field=models.ManyToManyField(
                blank=True,
                help_text='Projects this evidence chunk belongs to (inferred from source)',
                related_name='evidence_chunks',
                to='core.project',
                verbose_name='Projects'
            ),
        ),
        
        # Update project PII fields
        migrations.AlterModelOptions(
            name='project',
            options={'verbose_name': 'Project', 'verbose_name_plural': 'Projects'},
        ),
        
        # Update EvidenceSource PII fields  
        migrations.AlterModelOptions(
            name='evidencesource',
            options={'verbose_name': 'Evidence Source', 'verbose_name_plural': 'Evidence Sources'},
        ),
        
        # Update EvidenceFact PII fields
        migrations.AlterModelOptions(
            name='evidencefact',
            options={'verbose_name': 'Evidence Fact', 'verbose_name_plural': 'Evidence Facts'},
        ),
        
        # Update EvidenceInsight PII fields
        migrations.AlterModelOptions(
            name='evidenceinsight',
            options={'verbose_name': 'Evidence Insight', 'verbose_name_plural': 'Evidence Insights'},
        ),
        
        # Update Recommendation PII fields
        migrations.AlterModelOptions(
            name='recommendation',
            options={'verbose_name': 'Recommendation', 'verbose_name_plural': 'Recommendations'},
        ),
        
        # Remove some old indexes and add new ones
        migrations.RunSQL(
            "DROP INDEX IF EXISTS core_eviden_organiz_6361d6_idx;",
            reverse_sql="SELECT 1;"  # No reverse needed
        ),
        migrations.RunSQL(
            "DROP INDEX IF EXISTS core_eviden_priorit_631dd1_idx;",
            reverse_sql="SELECT 1;"  # No reverse needed
        ),
        
        # Add new indexes
        migrations.AddIndex(
            model_name='evidenceinsight',
            index=models.Index(fields=['organization', 'evidence_score'], name='core_evidenceinsight_org_score_idx'),
        ),
        migrations.AddIndex(
            model_name='evidenceinsight',
            index=models.Index(fields=['sentiment'], name='core_evidenceinsight_sentiment_idx'),
        ),
        migrations.AddIndex(
            model_name='recommendation',
            index=models.Index(fields=['organization', 'type'], name='core_recommendation_org_type_idx'),
        ),
        migrations.AddIndex(
            model_name='recommendation',
            index=models.Index(fields=['status'], name='core_recommendation_status_idx'),
        ),
        migrations.AddIndex(
            model_name='project',
            index=models.Index(fields=['organization', 'title'], name='core_project_org_title_idx'),
        ),
        migrations.AddIndex(
            model_name='evidencesource',
            index=models.Index(fields=['organization', 'type'], name='core_evidencesource_org_type_idx'),
        ),
        migrations.AddIndex(
            model_name='evidencefact',
            index=models.Index(fields=['organization', 'source'], name='core_evidencefact_org_source_idx'),
        ),
        migrations.AddIndex(
            model_name='evidencechunk',
            index=models.Index(fields=['organization', 'source'], name='core_evidencechunk_org_source_idx'),
        ),
    ]