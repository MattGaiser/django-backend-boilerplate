"""
Django management command to trigger a Prefect flow.
"""

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import requests
import json
import structlog

logger = structlog.get_logger(__name__)


class Command(BaseCommand):
    help = 'Trigger a Prefect flow execution'

    def add_arguments(self, parser):
        parser.add_argument(
            'flow_name',
            type=str,
            help='Name of the flow to execute'
        )
        parser.add_argument(
            '--parameters',
            type=str,
            nargs='*',
            help='Flow parameters in key=value format'
        )
        parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Request timeout in seconds (default: 30)'
        )
        parser.add_argument(
            '--wait',
            action='store_true',
            help='Wait for flow completion and show status'
        )

    def parse_parameters(self, param_strings):
        """Parse parameter strings in key=value format."""
        parameters = {}
        if param_strings:
            for param in param_strings:
                if '=' not in param:
                    raise CommandError(f'Invalid parameter format: {param}. Use key=value')
                
                key, value = param.split('=', 1)
                
                # Try to parse as JSON for complex types
                try:
                    parameters[key] = json.loads(value)
                except json.JSONDecodeError:
                    # Keep as string if not valid JSON
                    parameters[key] = value
                    
        return parameters

    def handle(self, *args, **options):
        prefect_api_url = getattr(settings, 'PREFECT_API_URL', None)
        
        if not prefect_api_url:
            raise CommandError('PREFECT_API_URL not configured in settings')

        flow_name = options['flow_name']
        
        try:
            parameters = self.parse_parameters(options.get('parameters', []))
        except CommandError:
            raise
        except Exception as e:
            raise CommandError(f'Error parsing parameters: {str(e)}')

        self.stdout.write(f'Triggering flow: {flow_name}')
        if parameters:
            self.stdout.write(f'Parameters: {json.dumps(parameters, indent=2)}')

        try:
            # First, get the flow ID by name
            flows_url = f"{prefect_api_url.rstrip('/')}/flows"
            response = requests.get(flows_url, timeout=options['timeout'])
            
            if response.status_code != 200:
                raise CommandError(f'Could not fetch flows: HTTP {response.status_code}')

            flows_data = response.json()
            flows = flows_data if isinstance(flows_data, list) else flows_data.get('flows', [])
            
            target_flow = None
            for flow in flows:
                if flow.get('name') == flow_name:
                    target_flow = flow
                    break
                    
            if not target_flow:
                available_flows = [flow.get('name', 'Unknown') for flow in flows]
                raise CommandError(
                    f'Flow "{flow_name}" not found. Available flows: {available_flows}'
                )

            flow_id = target_flow['id']
            self.stdout.write(f'Found flow ID: {flow_id}')

            # Create a flow run
            flow_runs_url = f"{prefect_api_url.rstrip('/')}/flow_runs"
            payload = {
                'flow_id': flow_id,
                'parameters': parameters
            }
            
            response = requests.post(
                flow_runs_url,
                json=payload,
                timeout=options['timeout']
            )
            
            if response.status_code in [200, 201]:
                run_data = response.json()
                run_id = run_data.get('id', 'Unknown')
                run_name = run_data.get('name', 'Unknown')
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Flow run created successfully')
                )
                self.stdout.write(f'Run ID: {run_id}')
                self.stdout.write(f'Run Name: {run_name}')
                
                logger.info("Prefect flow run created", 
                          flow_name=flow_name, 
                          flow_id=flow_id,
                          run_id=run_id,
                          parameters=parameters)
                
                # Optionally wait for completion
                if options['wait']:
                    self.wait_for_completion(prefect_api_url, run_id, options['timeout'])
                    
            else:
                error_msg = f'Failed to create flow run: HTTP {response.status_code}'
                try:
                    error_details = response.json()
                    error_msg += f' - {error_details}'
                except:
                    error_msg += f' - {response.text}'
                    
                raise CommandError(error_msg)
                
        except requests.exceptions.ConnectionError:
            raise CommandError('Could not connect to Prefect server')
            
        except requests.exceptions.Timeout:
            raise CommandError('Request to Prefect server timed out')
            
        except CommandError:
            raise
            
        except Exception as e:
            logger.error("Unexpected error running flow", 
                        flow_name=flow_name, error=str(e))
            raise CommandError(f'Unexpected error: {str(e)}')

    def wait_for_completion(self, api_url, run_id, timeout):
        """Wait for flow run completion and show status updates."""
        import time
        
        self.stdout.write('\nWaiting for flow completion...')
        
        max_attempts = timeout // 5  # Check every 5 seconds
        attempt = 0
        
        while attempt < max_attempts:
            try:
                run_url = f"{api_url.rstrip('/')}/flow_runs/{run_id}"
                response = requests.get(run_url, timeout=10)
                
                if response.status_code == 200:
                    run_data = response.json()
                    state = run_data.get('state', {})
                    state_name = state.get('name', 'Unknown')
                    
                    self.stdout.write(f'Status: {state_name}')
                    
                    if state_name in ['Completed', 'Failed', 'Cancelled']:
                        if state_name == 'Completed':
                            self.stdout.write(
                                self.style.SUCCESS('✅ Flow completed successfully')
                            )
                        else:
                            self.stdout.write(
                                self.style.ERROR(f'❌ Flow {state_name.lower()}')
                            )
                        break
                        
                time.sleep(5)
                attempt += 1
                
            except Exception as e:
                self.stdout.write(f'Error checking status: {str(e)}')
                break
                
        if attempt >= max_attempts:
            self.stdout.write('⏰ Timeout waiting for flow completion')