Here is a comprehensive `copilot-instructions.md` file that consolidates all the goals, standards, and architectural decisions discussed so far. This will guide GitHub Copilot (or any AI agent) in generating high-quality Django code that aligns with your long-term goals.

---

````markdown
# 🧠 Copilot Instructions for Django Development

This document defines the standards, architecture, and coding practices Copilot must follow when assisting with Django development. The goals are long-term maintainability, auditability, extensibility, and enterprise readiness from the start.

---

## ✅ Foundational Goals

- All models must support audit logging, soft delete, PII tracking, and multi-tenancy.
- All data access must respect role-based access control (RBAC) and organizational scope.
- The project must be ready for internationalization (i18n), API versioning, structured logging, and test automation from the outset.
- All testing must use Pytest and factories, with third-party integrations handled via VCR.py.
- Code must be modular, documented, and production-ready.

---

## 🏗️ Models and Database Design

### `BaseModel`
- All models must inherit from a common abstract `BaseModel`:
  - `id = UUIDField(primary_key=True)`
  - `created_at`, `updated_at` (timestamped)
  - `deleted_at` for soft delete
  - `created_by`, `updated_by` (linked via signal to current user)
  - `organization = ForeignKey(Organization)`
  - All fields must include `verbose_name` and `help_text`
  - Required: `Meta.pii_fields = [...]` for any model that includes PII

### Soft Delete
- Implemented via a nullable `deleted_at` field.
- Soft-deleted objects must be excluded from default querysets.
- Provide `.all_objects` and `.active_objects` managers.

### Slugs and URLs
- Models exposed via URL (e.g., Organization) must have a `slug` field.
- Implement `get_absolute_url()` for any model used in routes or links.

---

## 🔐 RBAC and Organizational Scope

### Organization & Membership
- Users are connected to organizations via a through model `OrganizationMembership`.
- Membership includes a `role` (ADMIN, MANAGER, VIEWER) using a shared enum.
- Users may belong to multiple orgs, with one marked as `is_default`.

### Permissions
- All data access must be scoped to the user’s role in the organization.
- Views must use a DRF permission class like:
  ```python
  class IsAuthenticatedAndInOrgWithRole:
      ...
````

* `User.get_role(org)` and `User.has_role(org, role)` helpers must be implemented.

---

## 🌐 Django REST Framework

* Use `rest_framework` with:

  * `IsAuthenticated` as default permission
  * `PageNumberPagination`
  * JSON-only rendering (no BrowsableAPIRenderer in prod)
  * URLPathVersioning (e.g., `/api/v1/`)
* All API endpoints must validate org membership and RBAC.
* Use viewsets and serializers organized under `api/v1/`

---

## 🌍 Internationalization (i18n)

* All strings must be wrapped in `gettext_lazy`.
* Provide `LANGUAGE_CODE = 'en'` and scaffolding for `'fr'`.
* Add translation for all model field labels and enums.

---

## 📚 Constants and Enums

* Create a shared `constants.py` or `enums.py`:

  * Use `TextChoices` for enums: `OrgRole`, `Plan`, `Language`, etc.
  * All choices must use `gettext_lazy` for i18n compatibility.

---

## 🧪 Testing and Developer Experience

* All tests must be written in **Pytest**.
* Use `factory_boy` for test data.
* Use `pytest-django` for model tests and API tests.
* Use `VCR.py` for all tests involving external APIs — no mocks for HTTP requests.
* Include fixtures for demo data (e.g., org, user, tags).
* Provide a one-command dev setup with Docker.

---

## 📦 Tagging System

* Tags should be implemented using `GenericForeignKey` and `GenericRelation`.
* Models that support tagging must inherit from `TaggableMixin`.

---

## 📈 Logging and Observability

* Use `structlog` or `python-json-logger` for structured logging.
* Include `request_id`, `user_id`, `org_id` in all log entries.
* Provide middleware to generate and attach `request_id` to thread-local storage.
* Ensure logs are JSON-formatted and compatible with centralized log aggregators.

---

## 🔄 Versioning and Change Tracking

* Expose version info via `/version.json`:

  * `commit`, `timestamp`, `branch`
* Generate `version.json` at build time via script
* Maintain a `CHANGELOG.md` using [Keep a Changelog](https://keepachangelog.com) format

---

## 🧠 Additional Guidelines

* Never use raw JSON fields for dynamic config — prefer normalized models.
* Never use default Django User — always use custom `User` model.
* All models, views, and serializers must be documented with docstrings.
* All admin interfaces should include `list_display`, `search_fields`, `readonly_fields`.

---

## 🔧 Tools to Be Used

| Purpose         | Tool / Library                       |
| --------------- | ------------------------------------ |
| API Framework   | Django REST Framework                |
| Testing         | Pytest, FactoryBoy, VCR.py           |
| Auth            | Custom User + OrganizationMembership |
| i18n            | gettext\_lazy + `makemessages`       |
| Logging         | structlog or python-json-logger      |
| API Versioning  | URLPathVersioning (`/api/v1/`)       |
| Slug Generation | slugify(name)                        |
| Permissions     | Custom DRF permission classes        |

---

## 📦 Future-Proofing (Track Separately)

* Feature flag framework
* Webhook system
* Fine-grained per-resource permissions
* Multi-region deployments
* Export/import support

---

This file should be kept in the project root as `copilot-instructions.md` and updated as architectural decisions evolve.

```

---

Let me know if you'd like this file committed alongside a `copilot.config.json` or need a shorter version for Copilot Chat onboarding.
```
