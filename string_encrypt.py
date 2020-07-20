import re

source_file = "payloadharness_backup.cpp"

def xor(data, key): 
	#data = bytearray(data)
	#key = bytearray(key)
	data_length = len(data)
	key_length = len(key)
	key_index = 1
	encrypted = ""
	for data_index, a in enumerate(data):
		key_index = data_index % key_length
		encrypted += chr(ord(a)^ord(key[key_index]))
	# print "Encrypting data: {} with key: {}".format(data, key)
	return encrypted

# need to hex encode strings in '\x
def hex_encode(string):
	# didnt need to reverse the string.. thought you had to cuz of endianess?
	return "".join([hex(ord(x)).replace("0x",r"\x") for x in string])

# TODO: return 
def get_string_arg(args_regex, line):
	args = []
	for key in args_regex.keys():
		pattern = args_regex[key]
		match = re.search(pattern, line)
		if match and match.group(1):
			args.append(match.group(1))
	if args:	
		return args

def main():
	# we are just looking to encrypt the following
	# 1. 2nd arg of getProcAddress
	# 2. 1st arg of getmodulehandle

	# Need to do two passes thru the code:
	# 1. First pass tracks all the strings to be encrypted, and generates a static char*[] that references the strings
	# 2. Second pass replaces all the tracked strings from the first step with their reference to the string table

	'''
	# Presentation Notes:
	TODO
	# Stick encrypted strings somewhere writable in memory: Right now the implementation will create a new decrypted string table on the heap, instead of decrypting
	the static encrypted strings in place. This is annoying because heap allocations are suspicious and can attract unwarranted attention to your decryption routine,
	but its a hack fix since C does not allow string literals to be modified; modifying them results in undefined behaviour according 
	to standards. Tried to modify them anyways by casting const char* back to char* and got access violation error: turns out C string literals are stored in the .rdata section
	which is always memory mapped with permissions readonly. 

	# We would need to write to r+w location on the stack

	# initially wanted to decrypt strings from static memory ie. rdata. Turns out the following C code doesn't work:
	(redo this example)
	const char* str_table[];
	str_table[0] = "hellostring"; // ERROR: cannot 
	
	Const
	'''
	# Actually can just combine into single pass
	# TODO: make this random seed; ie. system time; 
	key = "XORkey"

	# C code templates used to generate our encryption/decryption routines
	# needs to go at the top of the file after the includes
	# need following c libraries:
	#include <stdio.h>
	#include <stdlib.h>
	#include <string.h>
	decryption_routine_code = """
//TODO: make sure that null byte the doesnt mess up the decryption
# include <string.h>
# include <stdlib.h>
# include <stdio.h>

char* decrypt_text(const char* str_table[], int key_index) {
    const char* key;
    const char* data = str_table[key_index];
    if (key_index == 0) {
        key = "XORkey";
    }
    else {
        // use the previously decrypted string as the new key
        key = str_table[key_index - 1];
    }

    int data_length = strlen(data);
    int key_length = strlen(key);
    
    char* new_data = (char*)malloc(sizeof(char)* (data_length + 1));
    for (int i = 0; i < data_length; ++i) {
        new_data[i] = data[i] ^ key[i % key_length];
        printf("%c %c %c\\n", data[i], key[i % key_length], data[i] ^ key[i % key_length]);
    }

    new_data[data_length] = '\\0';
    return new_data;
}
	"""

	# 1. Initializes str_tbl (char* array)
	# 2. Initializes the encrypted variables
	# 3. Decryption routine
	init_code = ""
	args_regex = {
		# "getprocaddress" : r'GetProcAddress\(.*,\s*[\"\'](.*)[\"\']\s*\)'
		"getprocaddress" : r'GetProcAddress\(.*,\s*(.*)\s*\)'

		# fix this regex
		#"getmodulehandle" : r'GetModuleHandle[W|A]\(.?[\"\'](.*)[\"\']\s?\)'
	}

	modified_code = ""
	init_code = ""
	global_init_code = ""
	main_init_code = ""

	enc_strings = []
	# C code for generating our string table
	global_init_code += decryption_routine_code

	# need to do this in two passes we need to find out before hand if strings are being referenced in main
	# pass #1
	# iterate thru source file
	with open(source_file, "r") as source:
		lines = source.readlines()
		for line in lines:
			# remember stripping just \n will sring concatentation
			line = line.strip("\n").strip("\r")
			args = get_string_arg(args_regex, line)

			string_index = 0
			encoded_arg = ""
			if args:
				for arg in args:
					# replace references in the source code with our string table array entries
					line = line.replace(arg, "str_table[{}]".format(string_index))
					
					# we are going to generate the decryption code for arg
					# TODO: keep track of current indent level
					decrypt_str_code = "    " + "str_table[{}] = decrypt_text(str_table, {});\n".format(string_index, string_index)
					modified_code += decrypt_str_code

					arg = re.sub("[\"\']", "", arg)
					
					string_index += 1
					enc_strings.append(arg)

			# if we are at main function declaration
			modified_code += line + '\n'
	
	#TODO: to reference str_table in another linked file, just reference str_table as extern (=make it an as-of-yet nonresolved reference to a global scope variable defined in some other compilation unit)
	# extern const char* str_table[];
	# https://stackoverflow.com/questions/6792930/how-do-i-share-a-global-variable-between-c-files
	table_init_code = "const char* str_table[{}];\n"
	key_init_code = "const char* key = \"{}\";\n"

	global_init_code += table_init_code.format(len(enc_strings))
	global_init_code += key_init_code.format(key)

	# code for encrypting strings
	pass1_code = global_init_code + modified_code + init_code
	pass2_code = ""

	# used to find main
	main_seen = False
	left_bracket_seen = False

	# used to find end of includes
	# Implement some kind of iterable look ahead here
	# maybe tee (clones iterable allowing us to look ahead) from itertools

	#pass2 intializes str_table entries in main and the writes the decryption routine to the top of the file
	#after includes
	for line in pass1_code.split('\n'):
		pass2_code += line + '\n'

		if 'main(' in line:
			main_seen = True
		
		if '{' in line and main_seen:
			left_bracket_seen = True

		if main_seen and left_bracket_seen:
			for index, enc_string in enumerate(enc_strings):
				# generate static encrypted strings
				if index != 0:
					# we are using the n-1 string as the decryption key for string n
					key = enc_strings[index-1]
				
				encrypted_arg = xor(enc_string, key)
				encoded_arg = hex_encode(encrypted_arg)
				
				# TODO: keep track of current indent level
				pass2_code += "    " + "str_table[{}] = \"{}\";\n".format(index, encoded_arg)

				# Debugging Purposes Only
				pass2_code += "    " + "str_table[{}] = decrypt_text(str_table, {});\n".format(index, index)
				pass2_code += "    " + "printf(\"%s|\\n\", str_table[{}]);\n".format(index)

			main_seen = False
			left_bracket_seen = False
	print pass2_code


main()


# print "Actual Encrypt"
# key = "XORkey"
# print hex_encode(xor("LoadLibraryA", key))
# print hex_encode(xor("VirtualAllocEx", "LoadLibraryA"))