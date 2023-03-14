import CloudFlare
import yaml

# Helper functions
def load_yaml(file_path):
    with open(file_path) as file:
        return yaml.safe_load(file)

def is_reserved_record(name, reserved_records):
    for record in reserved_records:
        if name == record['name']:
            return True
    return False

# Load API Key from ky.yml
api_data = load_yaml('misc/ky.yml')
api_key = api_data['api_key']
zone_id = api_data['zone_id']

# Load subdomain YAML file
yaml_data = load_yaml('subdomain.yml')

# Get CNAME, NS, and A records from YAML
records = {
    'CNAME': yaml_data.get('CNAME records', []),
    'NS': yaml_data.get('NS records', []),
    'A': yaml_data.get('A records', [])
}

# Load record databases
record_dbs = {
    'CNAME': load_yaml('misc/cnamedb.yml'),
    'NS': load_yaml('misc/dbns.yml'),
    'A': load_yaml('misc/dba.yml')
}

# Set up Cloudflare API client
cf = CloudFlare.CloudFlare(email='', token=api_key)

# Loop through records and update or create them
for record_type, record_list in records.items():
    for record in record_list:
        name = record['name']
        value = record['value']
        ttl = record.get('ttl', 14400)
        proxy = record.get('proxy', False)

        # Check if the record is reserved
        if is_reserved_record(name, yaml_data.get('Reserved records', [])):
            print(f"{name} is a reserved name and cannot be modified")
            continue

        # Check if the record already exists in the DB
        existing_record = None
        for record in record_dbs.get(record_type + ' records', []):
            if name == record['name'] and value == record['value']:
                existing_record = record
                break

        # If the record already exists, skip it
        if existing_record:
            print(f"{name} already exists in the DNS records")
            continue

        # Otherwise, create the new record
        try:
            cf.zones.dns_records.post(zone_id, data={
                'type': record_type, 'name': name, 'content': value, 'ttl': ttl, 'proxied': proxy})
        except CloudFlare.exceptions.CloudFlareAPIError as e:
            print(f"Error creating record {name}: {e}")
            continue

        # Add the new record to the DB
        record_dbs.setdefault(record_type + ' records', []).append({'name': name, 'value': value})
        with open(f'misc/db{record_type.lower()}.yml', 'w') as file:
            yaml.dump(record_dbs, file)

        print(f"Record {name} created successfully")
