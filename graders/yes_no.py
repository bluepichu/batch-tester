from clint.textui import colored

def grade(expected_input, given_input):
	expected, given = expected_input, given_input

	expected = expected.split("\n")
	given = given.split("\n")

	if len(expected) != 1:
		raise Exception("Grader error: invalid expected answer.")

	expected = expected[0].split(" ")

	if len(expected) != 1 and not (len(expected) == 2 and expected[1] == ""):
		raise Exception("Grader error: invalid expected answer.")

	expected = expected[0]

	if expected.upper() != "YES" and expected.upper() != "NO":
		raise Exception("Grader error: invalid expected answer.")

	if len(given) != 1:
		return False, colored.red(given_input)

	given = given[0].split(" ")

	if len(given) != 1 and not (len(given) == 2 and given[1] == ""):
		return False, colored.red(given_input)

	given = given[0]

	if expected.upper() == given.upper():
		return True, colored.green(given)
	else:
		return False, colored.red(given)