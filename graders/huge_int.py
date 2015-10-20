def grade(expected_input, given_input):
	expected, given = expected_input, given_input

	try:
		expected = int(expected)
	except Exception as ex:
		raise Exception("Grader error: invalid expected answer.")

	try:
		given = int(expected)
	except Exception as ex:
		return False, colored.red(given)

	if given == expected:
		return True, colored.green(given)
	else:
		return False, colored.red(given)