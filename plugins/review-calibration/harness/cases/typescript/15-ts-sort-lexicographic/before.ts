function topScores(scores: number[]): number[] {
    return [...scores].sort((a, b) => b - a).slice(0, 3);
}
