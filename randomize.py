import os
import random
import io
import zipfile
import json
import sys

# Isn't using argparse for whatever reason but this is just making sure you put in the right arguments to the command line call
if len(sys.argv) >= 2:
	try:
		seed = int(sys.argv[1])
	except Exception:
		print('The seed "{}" is not an integer.'.format(sys.argv[1]))
		exit()
	random.seed(seed)
	datapack_name = 'random_loot_{}'.format(seed)
	datapack_desc = 'Loot Table Randomizer, Seed: {}'.format(seed)
else:
	print('If you want to use a specific randomizer seed integer, use: "python randomize.py <seed>"')
	datapack_name = 'random_loot'
	datapack_desc = 'Loot Table Randomizer'
	
datapack_filename = datapack_name + '.zip'

print('Generating datapack...')
	
# Actual stuff happening now
# file_list is the complete list of files from loot_tables
file_list = []
# remaining will be a list of files that need to be moved around
remaining = []

# Create a list of every file in loot_table, and store that list into both file_list and remaining
for dirpath, dirnames, filenames in os.walk('loot_tables'):
	for filename in filenames:
		file_list.append(os.path.join(dirpath, filename))
		remaining.append(os.path.join(dirpath, filename))
		
# file_dict is a dictionary (collection of keys:values) that will define how to shuffle around loot_tables
file_dict = {}

for file in file_list:
        # Randomly grab a file from remaining ...
	i = random.randint(0, len(remaining)-1)
        # ... and create a key:value pair of file_list:remaining(random)
	file_dict[file] = remaining[i]
        # Now remove the file from remaining so it's not processed again
	del remaining[i]
        # e.g.
        # Imagine a file_list and remaining containing ['file_1', 'file_2', 'file_3']
        # remaining[i] could be 'file_2'
        # Now place the pairing of 'file_1':'file_2' into file_dict
        # So file_dict is now {'file_1': 'file_2'}
        # Now the next time this runs, the only files in remaining are 'file_1' and 'file_3'
        # And the next iteration will be mapping 'file_2' to either of these remaining files
        # The second iteration could therefore have a file_dict of {'file_1': 'file_2', 'file_2': 'file_3'}
	
zipbytes = io.BytesIO()
zip = zipfile.ZipFile(zipbytes, 'w', zipfile.ZIP_DEFLATED, False)

# from_file is the key in file_dict
# e.g. In the key:value pair 'file_1':'file_2', it would be 'file_1'
for from_file in file_dict:
        # Copy the contents of the file into memory by using the variable contents
        # e.g. For the first element in file_list, we are getting the contents of 'file_1'
	with open(from_file) as file:
		contents = file.read()
		
        # (Presumably) write the file in /data/minecraft/ with our new file
        # .e.g For the first element in file_list, we are writing 'file_1' to 'data/minecraft/file_2'
	zip.writestr(os.path.join('data/minecraft/', file_dict[from_file]), contents)
	
# Some Minecraft metadata stuff I assume lol
zip.writestr('pack.mcmeta', json.dumps({'pack':{'pack_format':1, 'description':datapack_desc}}, indent=4))
zip.writestr('data/minecraft/tags/functions/load.json', json.dumps({'values':['{}:reset'.format(datapack_name)]}))
# SethBling please use argparse
zip.writestr('data/{}/functions/reset.mcfunction'.format(datapack_name), 'tellraw @a ["",{"text":"Loot table randomizer by SethBling","color":"green"}]')
	
zip.close()
# Actually write the data to a compressed zip file, because I assume this is what Minecraft wants
with open(datapack_filename, 'wb') as file:
	file.write(zipbytes.getvalue())
	
# Tada, we're done
print('Created datapack "{}"'.format(datapack_filename))

#This is Atticus testing out github
#Test post please ignore
