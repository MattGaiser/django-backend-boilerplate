# Translation Workflow

This document describes how to manage translations in the Django Backend Boilerplate.

## Overview

The application supports internationalization (i18n) with the following configuration:

- **Default Language**: English (`en`)
- **Supported Languages**: English (`en`) and French (`fr`)
- **Translation Files**: Located in `locale/` directory
- **Settings**: Configured in `DjangoBoilerplate/settings.py`

## Configuration

The following i18n settings are enabled:

```python
USE_I18N = True       # Enable internationalization
USE_L10N = True       # Enable localization
LANGUAGE_CODE = 'en'  # Default language

LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
```

The `LocaleMiddleware` is included in the middleware stack to handle language detection and switching.

## Working with Translations

### 1. Marking Strings for Translation

All user-facing strings should be wrapped with Django's translation functions:

#### In Python Code (Models, Views, etc.)

```python
from django.utils.translation import gettext_lazy as _

# For model fields
class MyModel(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_("Name"),
        help_text=_("Enter the name")
    )
    
    class Meta:
        verbose_name = _("My Model")
        verbose_name_plural = _("My Models")

# For choices
class StatusChoices(models.TextChoices):
    ACTIVE = 'active', _('Active')
    INACTIVE = 'inactive', _('Inactive')
```

#### In Templates

```html
{% load i18n %}

<h1>{% trans "Welcome" %}</h1>
<p>{% blocktrans %}Hello {{ user.name }}!{% endblocktrans %}</p>
```

### 2. Updating Translation Files

Use the custom management command to update and compile translations:

```bash
# Update all configured languages (currently just French)
python manage.py update_translations

# Update specific language(s)
python manage.py update_translations --language fr

# Update messages only (don't compile)
python manage.py update_translations --no-compile

# Get help
python manage.py update_translations --help
```

Alternatively, use Django's built-in commands:

```bash
# Extract translatable strings to .po files
python manage.py makemessages -l fr

# Compile .po files to .mo files
python manage.py compilemessages
```

### 3. Translating Strings

1. **Open the translation file**: `locale/fr/LC_MESSAGES/django.po`

2. **Translate strings**: Find empty `msgstr` entries and add translations:

```po
#: core/models.py:101
msgid "Organization"
msgstr "Organisation"

#: core/models.py:106
msgid "Name of the organization"
msgstr "Nom de l'organisation"
```

3. **Compile translations**: Run `python manage.py compilemessages` or `python manage.py update_translations`

### 4. Language Preferences

#### User-Level Language Preference

Each user has a `language` field that stores their preferred language:

```python
user = User.objects.get(email='user@example.com')
user.language = 'fr'
user.save()
```

#### Organization-Level Language Preference

Organizations can set a default language preference. Users will fall back to their organization's language if they haven't set a personal preference.

## Directory Structure

```
locale/
└── fr/
    └── LC_MESSAGES/
        ├── django.po  # Translation source file
        └── django.mo  # Compiled translation file
```

## Best Practices

### 1. Always Use Translation Functions

- Use `gettext_lazy as _` for model fields, admin configurations, and any strings that are evaluated at import time
- Use `gettext as _` for strings in views and functions that are evaluated at runtime
- Use `{% trans %}` and `{% blocktrans %}` in templates

### 2. Provide Context for Translators

```python
# Good: Provides context
help_text=_("Enter the user's full name (first and last name)")

# Less helpful: Ambiguous
help_text=_("Name")
```

### 3. Use Descriptive Message IDs

```python
# Good: Clear meaning
_("User account has been successfully created")

# Avoid: Ambiguous
_("Success")
```

### 4. Regular Updates

- Run `python manage.py update_translations` regularly during development
- Always compile translations before deployment
- Review translation files for completeness

## Testing Translations

The test suite includes i18n tests in `core/tests/test_i18n.py`:

```bash
# Run i18n tests
python manage.py test core.tests.test_i18n

# Test with specific language
LANGUAGE_CODE=fr python manage.py test core.tests.test_i18n
```

## Adding New Languages

1. **Add to LANGUAGES setting**:
```python
LANGUAGES = [
    ('en', 'English'),
    ('fr', 'Français'),
    ('es', 'Español'),  # Add Spanish
]
```

2. **Generate translation files**:
```bash
python manage.py makemessages -l es
```

3. **Update the management command** if you want it to automatically handle the new language.

## Deployment

1. **Ensure translations are compiled**:
```bash
python manage.py compilemessages
```

2. **Include locale files in deployment**: Make sure the `locale/` directory and `.mo` files are included in your deployment package.

3. **Set language preferences**: Configure default language preferences for your production environment.

## Troubleshooting

### Missing Translations

If translations aren't appearing:

1. Check that `USE_I18N = True` in settings
2. Verify `LocaleMiddleware` is in `MIDDLEWARE`
3. Ensure `.mo` files exist and are compiled: `python manage.py compilemessages`
4. Check that strings are properly wrapped with translation functions

### Command Issues

If the `update_translations` command fails:

1. Ensure `gettext` tools are installed: `apt-get install gettext`
2. Check file permissions on the `locale/` directory
3. Verify LOCALE_PATHS setting is correct

### Performance

- Compiled `.mo` files are cached by Django
- Use `gettext_lazy` for better performance in model definitions
- Consider using Django's translation caching for high-traffic sites

## Related Documentation

- [Django Internationalization Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/)
- [Django Translation Documentation](https://docs.djangoproject.com/en/stable/topics/i18n/translation/)
- [GNU gettext Documentation](https://www.gnu.org/software/gettext/manual/gettext.html)