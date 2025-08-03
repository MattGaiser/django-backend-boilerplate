# Testing Guide for PII Validation and Prefect Worker Fixes

This document provides testing instructions to verify that both issues have been resolved.

## 1. PII Validation Fix Testing

### Issue Fixed
The original error messages:
```
PII validation skipped for User: Model User contains PII fields {'email', 'full_name', 'last_login_ip'} that are not declared in pii_fields. Current pii_fields: set().
PII validation skipped for Organization: Model Organization contains PII fields {'name'} that are not declared in pii_fields. Current pii_fields: set().
PII validation skipped for Project: Model Project contains PII fields {'name'} that are not declared in pii_fields. Current pii_fields: set().
PII validation skipped for Tag: Model Tag contains PII fields {'name'} that are not declared in pii_fields. Current pii_fields: set().
```

### Changes Made
1. **Removed BaseModel.pii_fields**: Removed the empty `pii_fields = []` from BaseModel to prevent inheritance conflicts
2. **Fixed get_model_pii_fields()**: Updated to use `hasattr()` and return `None` for missing pii_fields instead of empty list
3. **Verified all models have proper declarations**:
   - **User**: `pii_fields = ['email', 'full_name', 'last_login_ip']`
   - **Organization**: `pii_fields = ['name']`
   - **Project**: `pii_fields = ['name']`
   - **Tag**: `pii_fields = ['name']`
   - **OrganizationMembership**: `pii_fields = []`

### Testing Steps
1. **Start the Django application**:
   ```bash
   docker compose up django db
   ```

2. **Check for PII validation errors**: 
   - ✅ **Expected**: No PII validation error messages in startup logs
   - ❌ **Before fix**: Multiple "PII validation skipped" error messages

3. **Verify the fix works**: Look for these log patterns:
   ```bash
   # Should NOT see these anymore:
   # "PII validation skipped for User"
   # "PII validation skipped for Organization" 
   # "PII validation skipped for Project"
   # "PII validation skipped for Tag"
   ```

## 2. Prefect Worker Connectivity Fix

### Issue Fixed
The original error: "This URL does not work: http://prefect-server:4200/work-pools/work-pool/default-pool"

### Root Cause
User was trying to access Prefect UI using internal Docker service name instead of localhost.

### Changes Made
1. **Created PREFECT_UI_ACCESS.md**: Comprehensive guide for accessing Prefect UI
2. **Documented correct URLs**:
   - ✅ **Correct**: http://localhost:4200
   - ❌ **Incorrect**: http://prefect-server:4200
3. **Added troubleshooting guide**

### Testing Steps
1. **Start all services**:
   ```bash
   docker compose up
   ```

2. **Wait for services to be healthy** (2-3 minutes on first startup)

3. **Test Prefect UI access**:
   - Open browser to: http://localhost:4200
   - ✅ **Expected**: Prefect UI loads successfully
   - Navigate to work pools: http://localhost:4200/work-pools
   - ✅ **Expected**: Can see "default-pool" work pool

4. **Verify worker connectivity**:
   ```bash
   docker compose logs prefect-agent
   ```
   - ✅ **Expected**: No connection errors
   - ✅ **Expected**: "Worker started" message appears

## 3. Quick Verification Commands

```bash
# Check that all services are running
docker compose ps

# Check Django startup logs for PII errors (should be none)
docker compose logs django | grep -i "pii validation"

# Check Prefect agent logs for connectivity (should be successful)
docker compose logs prefect-agent | tail -20

# Test Prefect API health
curl http://localhost:4200/api/health
```

## 4. Manual Testing Checklist

- [ ] Django starts without PII validation errors
- [ ] Prefect UI accessible at http://localhost:4200
- [ ] Work pools page shows "default-pool"
- [ ] Prefect agent connects successfully to server
- [ ] No "PII validation skipped" messages in logs

## Expected Results

After these fixes:
1. **Django startup**: Clean startup with no PII validation errors
2. **Prefect access**: UI accessible via http://localhost:4200 with working worker pool
3. **Documentation**: Clear guidance in PREFECT_UI_ACCESS.md for future users