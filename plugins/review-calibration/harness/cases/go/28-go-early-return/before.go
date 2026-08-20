package describe

func describe(n int) string {
	var result string
	if n < 0 {
		result = "negative"
	} else {
		result = "non-negative"
	}
	return result
}
