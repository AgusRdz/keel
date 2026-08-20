// go.mod: go 1.20 (pre-1.22 semantics: the `for` loop variable is reused across iterations)
package workers

func startWorkers(ids []int) {
	for _, id := range ids {
		id := id
		go func() {
			process(id)
		}()
	}
}
