from datetime import *
from time import sleep, perf_counter
from sys import exit
import os
from shutil import copyfile
import subprocess
from subprocess import *
from filecmp import *
from clint.textui import *
from psutil import *
from shutil import get_terminal_size
import json
import re
import argparse
import readline
from bs4 import BeautifulSoup
import requests

# TODO cleanup this import mess

with open("config.json") as config_file:
	config = json.load(config_file)

def grade_problem(problem, lang, contest_dir, args):
	for l in config["languages"]:
		if lang in config["languages"][l]["aliases"]:
			lang = l
			break
	else:
		return False

	with open(os.path.join(contest_dir, config["directories"]["descriptors"], problem + ".json")) as descriptor_file:
		descriptor = json.load(descriptor_file)

	lang = config["languages"][lang]
	
	if "compile" in lang:
		log(0, args.verbose, colored.magenta("\nCompiling...", bold=True), end="\r")
		try:
			compile = Popen(lang["compile"]%(os.path.join(contest_dir, config["directories"]["src"], lang["file"]%(problem)), os.path.join(contest_dir, config["directories"]["bin"])), stdout=PIPE, stderr=PIPE, cwd=contest_dir, universal_newlines=True, shell=True)
			out, err = compile.communicate(timeout=config["defaults"]["compile_timeout"])
			err = re.sub("Note:.+\n", "", err)
		except subprocess.TimeoutExpired:
			log(0, args.verbose, colored.magenta("Compilation timed out.", bold=True))
			compile.kill()
			return True
		else:
			if err != "":
				log(0, args.verbose, colored.magenta("Compilation error:\n" + err + "\n", bold=True))
				return True
			log(0, args.verbose, colored.magenta("Compilation successful.", bold=True))

	log(0, args.verbose, "")

	case_number = 1
	all_ok = True
	had_debug_output = False
	
	with open(os.path.join(contest_dir, "tests/%s"%(descriptor["testing"]["input_cases"]))) as cases:
		with open(os.path.join(contest_dir, "tests/%s"%(descriptor["testing"]["output_cases"]))) as expected_out:
			while True:
				line = cases.readline()
				if line == "":
					break
				try:
					log(1, args.verbose, colored.cyan("-"*(get_terminal_size()[0]-14)), colored.cyan("TEST CASE " + str(case_number) + "\n", bold=True))
					log_eq(0, args.verbose, colored.cyan("TEST CASE %2i: Running..."%(case_number)), end="")
					log(1, args.verbose, "Input:\n")
					inp = []
					while line != "---\n" and line != "---":
						inp.append(line)
						line = cases.readline()
					log(1, args.verbose, "".join([str(colored.white(line, bold=True)) if len(line) < get_terminal_size()[0] else str(colored.white(line[:(get_terminal_size()[0]-3)], bold=True) + colored.white("...")) for line in inp[:20]]), end="")
					if len(inp) > 20:
						log(1, args.verbose, colored.white("..."))
					log(1, args.verbose, "\n  (Total %i lines.)\n"%(len(inp)))
					log(1, args.verbose, colored.magenta("Running...", bold=True), end="\r")
					start_time = perf_counter()
					if descriptor["io"]["input"] != "stdin":
						with open(os.path.join(contest_dir, "bin/%s"%(descriptor["io"]["input"])), "w") as prog_in:
							prog_in.write("".join(inp))
					run = Popen(lang["run"]%(problem), stderr=PIPE, stdin=PIPE, stdout=PIPE, cwd=os.path.join(contest_dir, config["directories"]["bin"]), universal_newlines=True, shell=True)
					
					time_limit = args.timelimit or descriptor["limits"]["time"]

					try:
						if descriptor["io"]["input"] == "stdin":
							out, err = run.communicate(input="".join(inp), timeout=time_limit)
						else:
							out, err = run.communicate(timeout=time_limit)
						end_time = perf_counter()
					except subprocess.TimeoutExpired:
						end_time = perf_counter()
						run.kill()
						log(1, args.verbose, colored.magenta("Run timed out.\n", bold=True))
						print_verdict(case_number, "TLE", int(1000*(end_time - start_time)), args)
						all_ok = False
						line = expected_out.readline()
						while line != "---\n" and line != "---":
							line = expected_out.readline()
						if args.stop:
							return True
					else:
						if err:
							log(1, args.verbose, colored.magenta("Run exited with runtime error.\n", bold=True))
							log(1, args.verbose, colored.red(str(err)))
							log(1, args.verbose, "")
							log(1, args.verbose, "Output:")
							log(1, args.verbose, out)
							log(1, args.verbose, "")
							print_verdict(case_number, "RE", int(1000*(end_time - start_time)), args)
							all_ok = False
							if args.stop:
								return True
						else:
							log(1, args.verbose, colored.magenta("Run complete.", bold=True))
							log_eq(0, args.verbose, "\r" + " " * 32 + "\r" + colored.blue("TEST CASE %2i: Checking..."%(case_number)), end="")

							table_column_width = int((get_terminal_size()[0]-7)/2)

							log(1, args.verbose, "\nOutput:\n")
							log(1, args.verbose, ("  {0:" + str(table_column_width) + "} | {1:" + str(table_column_width) + "}").format("Expected Output", "Given Output"))
							log(1, args.verbose, " " + "-"*(table_column_width+2) + "+" + "-"*(table_column_width+2))
							
							out = out.split("\n")

							if out[-1] == "":
								out = out[:-1]

							debug_output = [line[1:] for line in out if len(line) > 0 and line[0] == "~"]
							answer_output = [line + "\n" for line in out if len(line) == 0 or line[0] != "~"]

							if descriptor["io"]["output"] != "stdout":
								with open(os.path.join(contest_dir, "bin/%s"%(descriptor["io"]["output"]))) as prog_out:
									answer_output = [line + "\n" for line in prog_out.read().split("\n")]
									if answer_output[-1] == "\n":
										answer_output = answer_output[:-1]

							line = expected_out.readline()
							correct = []
							while line != "---\n" and line != "---":
								correct.append(line)
								line = expected_out.readline()
							
							submission_correct = True

							for i in range(min(20, max(len(answer_output), len(correct)))):
								correct_line = correct[i] if i < len(correct) else ""
								given_line = answer_output[i] if i < len(answer_output) else ""
								
								if graders[descriptor["testing"]["grading"]](correct_line, given_line):                        
									log(1, args.verbose, "  {0} | {1}".format(
										show_whitespace(correct_line, True) + (" "*(table_column_width-len(correct_line)))
											if len(correct_line) <= table_column_width
										else show_whitespace(correct_line[:(table_column_width-3)] + "...", True),
										show_whitespace(given_line, True) + (" "*(table_column_width-len(given_line)))
											if len(given_line) <= table_column_width
										else show_whitespace(given_line[:(table_column_width-3)] + "...", True)))
								else:
									submission_correct = False
									log(1, args.verbose, "  {0} | {1}".format(
										show_whitespace(correct_line, False) + (" "*(table_column_width-len(correct_line)))
											if len(correct_line) <= table_column_width
										else show_whitespace(correct_line[:(table_column_width-3)] + "...", False),
										show_whitespace(given_line, False) + (" "*(table_column_width-len(given_line)))
											if len(given_line) <= table_column_width
										else show_whitespace(given_line[:(table_column_width-3)] + "...", False)))
							
							log(1, args.verbose, "\n (Expected", len(correct), "lines, given", len(correct), "lines)\n")
							
							if len(debug_output) > 0:
								log(1, args.verbose, "Debug Output:")
								log(1, args.verbose, "")
								for line in debug_output:
									log(1, args.verbose, " " + line)
								log(1, args.verbose, "")
								had_debug_output = True
							
							if submission_correct:
								print_verdict(case_number, "OK", int(1000*(end_time - start_time)), args)
							else:
								print_verdict(case_number, "WA", int(1000*(end_time - start_time)), args)
								all_ok = False
								if args.stop:
									return True
								
					case_number += 1
				except Exception as error:
					log(1, args.verbose, "Python error: ", error)
					raise Exception
	log(1, args.verbose, colored.cyan("\n" + "-"*get_terminal_size()[0]))
	if all_ok:
		log_eq(0, args.verbose, "")
		log(0, args.verbose, colored.green("***** CORRECT FOR ALL GIVEN CASES! *****"))
		if had_debug_output:
			log(0, args.verbose, colored.yellow(" ------> DON'T FORGET TO HANDLE DEBUG STATEMENTS! <------ "))
	return True

def print_verdict(case_number, verdict, time, args):
	color = colored.green if verdict == "OK" else colored.red
	log(1, args.verbose, "Verdict:", color(verdict + " (%ims)"%(time)))
	log_eq(0, args.verbose, "\r", " "*32, "\r" + color("TEST CASE %2i: %s (%ims)"%(case_number, verdict, time)))

def gr_exact(correct, given):
	return correct == given

def gr_error_3(correct, given):
	correct = float(correct)
	given = float(given)
	return abs(correct - given) / max(correct, 1) < 1e-3

def gr_error_6(correct, given):
	correct = float(correct)
	given = float(given)
	return abs(correct - given) / max(correct, 1) < 1e-6

graders = {
	"exact": gr_exact,
	"error3": gr_error_3,
	"error_6": gr_error_6
}

def add_file(args, contest_dir):
	problem = args.problem
	lang = args.language
	url = args.url
	for l in config["languages"]:
		if lang in config["languages"][l]["aliases"]:
			lang = l
			break
	else:
		return False
	with open(config["languages"][lang]["template"]) as template:
		with open(os.path.join(contest_dir, config["directories"]["src"], config["languages"][lang]["file"]%(problem)), "w") as solution_file:
			line = template.readline()
			while line != "":
				solution_file.write(line.replace("$PROBLEM_NAME", problem))
				line = template.readline()
	with open(os.path.join(contest_dir, config["directories"]["descriptors"], problem + ".json"), "w") as descriptor_file:
		descriptor = {
			"name": problem, # is this even used for anything?
			"io": {
				"input": "stdin",
				"output": "stdout",
			},
			"testing": {
				"input_cases": problem + ".in",
				"output_cases": problem + ".out",
				"grading": "exact"
			},
			"limits": {
				"time": 2,
				"memory": 64
			}
		}
		descriptor_file.write(json.dumps(descriptor, sort_keys=False, indent="\t", separators=(",", ": ")))
	if url:
		data = requests.get(url)
		if data:
			soup = BeautifulSoup(data.text, "html.parser")

			inputs = [strip_case(case) for case in soup.select("div.input pre")]
			outputs = [strip_case(case) for case in soup.select("div.output pre")]

			with open(os.path.join(contest_dir, "tests", problem + ".in"), "w") as inputs_file:
				for inp in inputs:
					inputs_file.write(inp)
					inputs_file.write("---\n")

			with open(os.path.join(contest_dir, "tests", problem + ".out"), "w") as outputs_file:
				for out in outputs:
					outputs_file.write(out)
					outputs_file.write("---\n")
	else:
		open(os.path.join(contest_dir, "tests", problem + ".in"), "a").close()
		open(os.path.join(contest_dir, "tests", problem + ".out"), "a").close()
	return True

def strip_case(elem):
    text = ""
    for e in elem.recursiveChildGenerator():
        if isinstance(e, str):
            text += e.strip()
        elif e.name == "br":
            text += "\n"
    return text

def log(level, log_level, *message, sep=" ", end="\n"):
	if level <= log_level:
		print(*message, sep=sep, end=end)

def log_eq(level, log_level, *message, sep=" ", end="\n"):
	if level == log_level:
		print(*message, sep=sep, end=end)

def show_whitespace(string, ok):
	ret = ""
	color = colored.green if ok else colored.red
	characters_in_line = 0
	for ch in string:
		if ch == " ":
			ret += color(u"\u00b7")
			characters_in_line += 1
		elif ch == "\n":
			ret += color(u"\u21a9")
			characters_in_line = 0
		elif ch == "\t":
			if characters_in_line % 4 == 0:
				ret += color(u"\u2576\u2500\u2500\u2574")
				characters_in_line += 4
			elif characters_in_line % 4 == 1:
				ret += color(u"\u2576\u2500\u2574")
				characters_in_line += 3
			elif characters_in_line % 4 == 2:
				ret += color(u"\u2576\u2574")
				characters_in_line += 2
			else:
				ret += color(u"\u2010")
				characters_in_line += 1
		else:
			ret += color(ch, bold=True)
			characters_in_line += 1
	return ret

def main():
	print(colored.blue("\nWelcome to the program batch tester!\n"))

	print("Language Options:")
	
	for lang in config["languages"]:
		print("  %s (%s)"%(lang, ", ".join(config["languages"][lang]["aliases"])))

	print()
	
	contest = input("Contest name: ")
	print()
	
	contest_dir = os.path.join(config["directories"]["root"], config["directories"]["contest"]%(contest))

	if not os.path.isdir(contest_dir):
		os.makedirs(contest_dir)
	if not os.path.isdir(os.path.join(contest_dir, "src")):
		os.makedirs(os.path.join(contest_dir, "src"))
	if not os.path.isdir(os.path.join(contest_dir, "bin")):
		os.makedirs(os.path.join(contest_dir, "bin"))
	if not os.path.isdir(os.path.join(contest_dir, "descriptors")):
		os.makedirs(os.path.join(contest_dir, "descriptors"))
	if not os.path.isdir(os.path.join(contest_dir, "tests")):
		os.makedirs(os.path.join(contest_dir, "tests"))

	argument_parser = argparse.ArgumentParser()

	argument_parser.add_argument("command")
	argument_parser.add_argument("problem")
	argument_parser.add_argument("language")

	argument_parser.add_argument("-v", "--verbose", action="count")
	argument_parser.add_argument("-s", "--stop", action="store_true")
	argument_parser.add_argument("-t", "--timelimit", type=float)
	argument_parser.add_argument("-u", "--url", type=str)

	while True:
		try:
			print()
			
			try:
				args = argument_parser.parse_args(input("> ").split(" "))
			except SystemExit:
				continue

			if args.verbose is None:
				args.verbose = 0
			
			if args.command == "quit":
				exit()

			if args.command == "clear" or args.command == "cls":
				os.system("cls" if os.name == "nt" else "clear")

			if args.command == "add":
				if not add_file(args, contest_dir):
					print("Unknown or unsupported language.  Add it to your config file if you would like to support it.\n")

			if args.command == "test":
				if not grade_problem(args.problem, args.language, contest_dir, args):
					print("Unknown or unsupported language.  Add it to your config file if you would like to support it.\n")
		except KeyboardInterrupt:
			print(colored.red("Operation stopped by keyboard interrupt.  Use \"quit\" or Ctrl+D to exit.", bold=True))
		except EOFError:
			exit()
if __name__ == "__main__": main()
