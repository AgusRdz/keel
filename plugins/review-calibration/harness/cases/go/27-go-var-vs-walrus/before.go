package sums

func computeTotal(items []int) int {
	var total int
	for _, v := range items {
		total += v
	}
	return total
}
