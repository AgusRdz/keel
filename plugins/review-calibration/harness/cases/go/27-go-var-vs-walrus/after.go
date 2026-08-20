package sums

func computeTotal(items []int) int {
	total := 0
	for _, v := range items {
		total += v
	}
	return total
}
