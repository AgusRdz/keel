function topScores(scores: number[]): number[] {
    return [...scores].sort().slice(0, 3);
}
