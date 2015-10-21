from clint.textui import colored

def grade(expected_input, given_input):
	expected, given = expected_input, given_input

	try:
		expected = int(expected)
	except Exception as ex:
		raise Exception("Grader error: invalid expected answer.")

	try:
		given = int(given)
	except Exception as ex:
		return False, colored.red(given_input)

	if given == expected:
		return True, colored.green(given_input)
	else:
		return False, colored.red(given_input)