use std::fs;
use std::env;
use regex::Regex;

// Read up on:
// Slicing


// patterns to replace in source
const replace_pats: &'static [&'static str] = &[r"GetProcAddress\(.*,\s*(.*)\s*\)"];

fn match_string(line:&str) -> Vec<&str> {
	let mut matched:Vec<&str> = Vec::new();
	for p in replace_pats {
		let pat = Regex::new(p).unwrap();
		// is there no better way to handle this?
		// Get someone's opinion on this
		let arg = pat.captures(line);
		match arg {
			None 	=> continue,
			Some(x) => {
				let matched_arg = x.get(1)
					.expect("Error getting first matching group")
					.as_str();
				matched.push(matched_arg);
			}
		}
	}
	matched
}

// implement a trait for std::String that allows for python like templating
// ie. iterates over a string and replaces all occurences of {} with values in a list 

// self is the current module (when dealing with paths) or the current object. 
// &self is a reference the the current object, useful if you want to use the object but not take ownership. 
// Self refers to the type of the current object.
pub trait format {
    fn format(&mut self, args:Vec<&str>);
}

impl format for String {
	fn format(&mut self, args:Vec<&str>) {
		let num_format = self.split('\n');
		println!("{:?}", num_format);
	}
}

fn main() {
	let table_init_code = String::from("ell");
	// most io operations in std returns Result<T,E>
	//	enum Result<T, E> {
 	//  	Ok(T),
   	//		Err(E),
	//	}
	
	// The both Ok(T) and Err(E) are of type Result; called enum invariants

	let path = env::current_dir().unwrap();
	// could handle with unwrap() which either returns T or panics if E
	// let mut path = match path {
	// 	Ok(blah) => Ok(blah),
	// 	Err(e) => Err(e),
	// };

	println!("Curr dir: {:?}\n", path);
	
	let filename = "./PayloadHarness.cpp";
	let contents: String = fs::read_to_string(filename)
		.expect("Done goofed"); //same as unrwap but can set custom message
		
	let lines:Vec<&str> = contents.split("\n").collect();
	
	// 	let contents: Vec<&str> = fs::read_to_string(filename)
		// .expect("Done goofed") //same as unrwap but can set custom message
		// .split("\n")
		// .collect();work if contents were not used again for the rest of the code
		
	// Doesnt work because fs:read_to_string returns a string that is not bound to anything (because content is bound to the end result after collect)
	// collect returns a Vec<&str> which, where the &str references something (the ret of read_to_string) that has gone out of scope (since it is not bound to anything)
	// Actually above code would 
	for line in lines{
		let get_proc_arg = match_string(line);
		for arg in get_proc_arg {
			println!("{}", arg);
			let str1 = String::from("helo\nworld").format(Vec::new());
		}
	}
}
