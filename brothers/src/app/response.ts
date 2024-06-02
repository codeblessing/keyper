export interface EntityResponse {
    id: string,
    url: string,
    status: "uploaded" | "processed"
    results: Array<Result>
}

export interface Result {
    x: number,
    y: number,
    w: number,
    h: number,
    label: string,
    confidence: number
}