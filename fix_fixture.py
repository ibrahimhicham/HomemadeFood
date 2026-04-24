import json

with open('initial_data_fixture.json', 'r') as f:
    fixture = json.load(f)

# Add updated_at to all entries that have created_at but missing updated_at
# Also fix image_url -> image for DishImage entries
fixed_count = 0
for item in fixture:
    if 'created_at' in item['fields'] and 'updated_at' not in item['fields']:
        item['fields']['updated_at'] = item['fields']['created_at']
        print(f'Added updated_at to {item["model"]} pk={item["pk"]}')
        fixed_count += 1
    
    # Fix image_url -> image for DishImage
    if item['model'] == 'dishes.dishimage' and 'image_url' in item['fields']:
        item['fields']['image'] = item['fields'].pop('image_url')
        print(f'Fixed image_url -> image for {item["model"]} pk={item["pk"]}')

with open('initial_data_fixture.json', 'w') as f:
    json.dump(fixture, f, indent=2)

print(f'Fixed {fixed_count} entries!')
