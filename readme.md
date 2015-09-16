# Batch Tester

If you're like me, you do a lot of programming competitions.  If you don't want a bunch of incorrect submissions, these require some method of testing your code before you submit it.  While you could test cases by hand, using a script to batch-test is a much smarter method.

# Usage

I suggest you clone this project to use it, and use pulls later to update.

## Config

Before you use the script, you'll need to setup a `config.json` file.  Here's what that would look like:

````json
{
	"languages": {
		"Java 8": { // the name of the language
			"aliases": ["java", "j8"], // how you'll access the language
			"template": "templates/template.java", // template file; see below
			"file": "%s.java", // what the file should be called
			"compile": "javac %s -d %s", // the compile statement (if applicable)
			"run": "java %s" // the run statement
		},
		"Python 3": {
			"aliases": ["python", "py"],
			"template": "templates/template.py",
			"file": "%s.py",
			"run": "python3 %s"
		}
	},
	"directories": {
		"root": "/Programming/Competitions", // path to root directory for contests
		"contest": "%s", // what to name a contest directory
		"src": "src", // what to name a source directory
		"bin": "bin" // what to name a binary directory
	},
	"defaults": {
		"compile_timeout": 15 // how long to wait for compilation
	}
}
````

## Templates

You can also include templates for your source files.  To use them, set a "template" property on the language object in the config file with the path to your template *relative to the script itself* (or just use an absolute path).

## Install Packages

Some pip packages are required to run the testing script.  To install them, use

````
pip install -r requirements.txt
````

## Usage

To start the script, use

````
python tester.py
````

Please note that only python 3.x is supported at the moment.

Once the script is started, you will be prompted to enter a contest name.  This name will correspond to the directory in which all of the contest files are stored.  (I personally recommend something like `315D1` for Codeforces #315, Division 1, for example, but it's really up to you.)

After you've entered a contest name, you're presented with a command line.  You can type "help" for a full list of commands from there, or I have listed them below:

- `add problem lang` - Creates new problem files for the given problem in the given language.  This will add three files: the source file itself, a test cases input file, and a test cases output file.

- `test problem lang` - Tests a solution using the test cases in the test cases input file and checking against the answers in the test cases output file.